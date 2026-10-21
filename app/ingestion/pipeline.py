from pathlib import Path
import shutil

from app.ingestion.chunker import chunk_document
from app.ingestion.chunk_store import PostgresChunkStore
from app.ingestion.parsers import PdfParseError, parse_document
from app.ingestion.registration import RegistrationStore
from app.ingestion.storage import resolve_storage_uri
from app.schema import (
    DocumentIngestionRequest,
    DocumentIngestionResult,
    IngestionStatus,
)


class IngestionPipeline:
    """Coordinates document registration and local document processing."""

    def __init__(
        self,
        registration_store: RegistrationStore,
        chunk_store: PostgresChunkStore,
        quarantine_dir: str | Path = "data/quarantine",
    ) -> None:
        self._registration_store = registration_store
        self._chunk_store = chunk_store
        self._quarantine_dir = Path(quarantine_dir)

    def register(
        self,
        request: DocumentIngestionRequest,
    ) -> DocumentIngestionResult:
        """Validate local storage before registering an upload."""
        resolve_storage_uri(request.storage_uri)
        return self._registration_store.register(request)

    def process(
        self,
        request: DocumentIngestionRequest,
        registration: DocumentIngestionResult | None = None,
    ) -> DocumentIngestionResult:
        """Process a canonical document while skipping duplicates and retries."""

        # Resolve a registration result supplied by the caller first.
        if registration is not None:
            if registration.status == IngestionStatus.DUPLICATE:
                return registration

            if registration.document_id != request.document_id:
                raise ValueError(
                    "Registration document_id does not match request."
                )

        # Look up this document before registering it again.
        registered = self._registration_store.get_registered_document(
            request.document_id
        )

        if registered is not None:
            registered_request, current_status = registered

            # Prevent a document ID from being reused for different content.
            if (
                registered_request.collection_id != request.collection_id
                or registered_request.content_sha256.lower()
                != request.content_sha256.lower()
            ):
                raise ValueError(
                    "Document ID is already registered with different content."
                )

            # A completed document must not be parsed or chunked again.
            if current_status == IngestionStatus.COMPLETED:
                return DocumentIngestionResult(
                    document_id=request.document_id,
                    collection_id=request.collection_id,
                    status=IngestionStatus.COMPLETED,
                    content_sha256=request.content_sha256.lower(),
                )

            # Do not process a document that was already quarantined.
            if current_status == IngestionStatus.QUARANTINED:
                return DocumentIngestionResult(
                    document_id=request.document_id,
                    collection_id=request.collection_id,
                    status=IngestionStatus.QUARANTINED,
                    content_sha256=request.content_sha256.lower(),
                )

            if current_status != IngestionStatus.QUEUED:
                raise ValueError(
                    f"Document cannot be processed from status "
                    f"{current_status.value!r}."
                )

        else:
            # Registration determines whether this is new content or a duplicate.
            resolved_registration = self.register(request)

            if resolved_registration.status == IngestionStatus.DUPLICATE:
                return resolved_registration

            # An idempotency-key retry may resolve to another canonical ID.
            if resolved_registration.document_id != request.document_id:
                return resolved_registration

            if resolved_registration.status != IngestionStatus.QUEUED:
                return resolved_registration

        path = resolve_storage_uri(request.storage_uri)

        try:
            parsed_document = parse_document(path)

        except PdfParseError as exc:
            try:
                self._quarantine_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                # Find an unused filename without overwriting existing files.
                destination = self._quarantine_dir / path.name
                counter = 1

                while destination.exists():
                    destination = self._quarantine_dir / (
                        f"{path.stem}-{request.document_id}-{counter}"
                        f"{path.suffix}"
                    )
                    counter += 1

                shutil.move(str(path), str(destination))

            except OSError as move_error:
                raise RuntimeError(
                    "Failed to move malformed document to quarantine: "
                    f"{move_error}"
                ) from move_error

            self._registration_store.set_status(
                request.document_id,
                IngestionStatus.QUARANTINED,
            )

            return DocumentIngestionResult(
                document_id=request.document_id,
                collection_id=request.collection_id,
                status=IngestionStatus.QUARANTINED,
                content_sha256=request.content_sha256.lower(),
                error_message=str(exc),
                quarantine_uri=destination.resolve().as_uri(),
            )

        chunks = chunk_document(
            parsed_document,
            document_id=request.document_id,
            collection_id=request.collection_id,
        )

        self._chunk_store.replace_document_chunks(
            request.document_id,
            request.collection_id,
            chunks,
        )

        self._registration_store.set_status(
            request.document_id,
            IngestionStatus.COMPLETED,
        )

        return DocumentIngestionResult(
            document_id=request.document_id,
            collection_id=request.collection_id,
            status=IngestionStatus.COMPLETED,
            content_sha256=request.content_sha256.lower(),
            extracted_pages=len(parsed_document.pages),
            chunk_ids=[chunk.chunk_id for chunk in chunks],
            warnings=list(parsed_document.warnings),
        )