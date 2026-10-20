
import argparse
import os
import sys

import psycopg


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the status of an ingested document."
    )
    parser.add_argument("document_id", help="Document ID to inspect")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not configured.", file=sys.stderr)
        return 2

    try:
        with psycopg.connect(database_url, connect_timeout=5) as conn:
            row = conn.execute(
                """
                SELECT
                    d.document_id,
                    d.collection_id,
                    d.status,
                    d.created_at,
                    COUNT(c.chunk_id) AS chunk_count
                FROM ingestion_documents AS d
                LEFT JOIN document_chunks AS c
                    ON c.document_id = d.document_id
                    AND c.collection_id = d.collection_id
                WHERE d.document_id = %s
                GROUP BY
                    d.document_id,
                    d.collection_id,
                    d.status,
                    d.created_at
                """,
                (args.document_id,),
            ).fetchone()

        if row is None:
            print(f"Document not found: {args.document_id}")
            return 1

        document_id, collection_id, status, created_at, chunk_count = row
        print(f"Document ID:  {document_id}")
        print(f"Collection:   {collection_id}")
        print(f"Status:       {status}")
        print(f"Created at:   {created_at.isoformat()}")
        print(f"Chunk count:  {chunk_count}")
        return 0

    except psycopg.Error:
        print("ERROR: Could not query PostgreSQL.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
