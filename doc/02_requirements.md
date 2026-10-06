EVALUATION TARGETS

it should generate the research report till the level of buying a paid report like if i will take a subscription or an analysist will analysie a comapny 

Your "paid analyst report" idea should become a quality rubric

This is actually a good north-star, provided we don't pretend it's objective.

Create a report-quality rubric:

Dimension	What we evaluate
Coverage	Did it address the research question?
Evidence	Are important claims supported?
Correctness	Are the claims factually correct?
Reasoning	Does the conclusion follow from evidence?
Financial analysis	Are financial trends interpreted correctly?
Valuation	Are assumptions explicit and calculations correct?
Contradictions	Are conflicting sources surfaced?
Uncertainty	Does it distinguish known/unknown/uncertain?
Citations	Can every material claim be traced to evidence?
Structure	Is the report usable by a human analyst?



Retrieval:
-For each benchmark question, the retrieval system must return the evidence required to answer the question, with the known relevant source appearing in the top-k results.

Answer:
- it should generate a well precised report also around its valuation that what one should do like kind of valaution upside downside thesis and antythesis 

Fallback:
- no 

Performance:
- it should be good 


MVP RESEARCH AREAS

MUST HAVE:
- industry analysis 
management overview 
fundamental analysis 


DEFERRED:
-


MCP TOOLS

MUST HAVE:
rag retrieval if annual report is summited in pdf format 
financial tool for financial analysis yahu finance 
ddgs or tavily for websearch and finding web information related data 
Company metadata tool
Calculator / financial computation
Source/citation store

DEFERRED:
-


Valuation

Current/reference valuation
Valuation methodology used
Assumptions
Base case
Bull case
Bear case
Implied valuation/range
Key sensitivities
Evidence supporting assumptions


Thesis

Evidence supporting the business case.

Antithesis

Evidence that could invalidate the thesis.

Decision context

What would need to be true for the bull/base/bear scenario to materialize?

Not:

"BUY / SELL / HOLD."

This keeps the project as a research and analysis platform, as originally defined.

1. Document Retrieval
   └── PDF → chunks → hybrid retrieval → reranking

2. Financial Data
   └── Yahoo Finance / selected financial API

3. Web Search
   └── Tavily or DDGS

4. Company Metadata
   └── ticker, company name, exchange, sector, etc.

5. Financial Calculator
   └── deterministic calculations

6. Source / Citation Management
   └── provenance + evidence references


   we are going to use langgraph and langfuse too 


   Your actual MVP scope

Based on what you've said, I'd challenge you to freeze something approximately like this:

MUST HAVE

Research

Company overview
Industry analysis
Management overview
Business model
Fundamental analysis
Financial statement analysis
Revenue/profit/cash-flow trends
Balance-sheet analysis
Management commentary
Competitive context
Risks
Valuation analysis
Bull/base/bear scenarios
Thesis + antithesis
Missing information
Conflicting information

Evidence

PDF filing ingestion
Hybrid retrieval
Reranking
Source provenance
Claim → evidence mapping
Citations
Evidence sufficiency detection

Research workflow

Research question
Task decomposition
Retrieval
Gap detection
Bounded follow-up research
Evidence reconciliation
Structured report
Persisted research state

Infrastructure

FastAPI
PostgreSQL + pgvector
BM25
Redis
API worker
Streamlit
Caddy
MCP tool layer

Evaluation

40-question benchmark
Retrieval metrics
Answer metrics
Unanswerable questions
Poisoned documents
A/B experiments
Regression dataset
7. DEFERRED

You should actually have things in this section.

I'd put:

Authentication
Multi-user accounts
Multi-tenancy
Portfolio tracking
Real-time market monitoring
Autonomous trading
Buy/sell execution
Broker integration
Personalized investment advice
Continuous autonomous research
Mobile application
Multiple document formats
Large-scale distributed workers
Kafka/Celery
Fine-tuning
Complex agent memory
Real-time streaming research
Automated investment recommendations

This is important because scope control is part of the engineering skill you're trying to practice.



the output format 

Your actual MVP scope

Based on what you've said, I'd challenge you to freeze something approximately like this:

MUST HAVE

Research

Company overview
Industry analysis
Management overview
Business model
Fundamental analysis
Financial statement analysis
Revenue/profit/cash-flow trends
Balance-sheet analysis
Management commentary
Competitive context
Risks
Valuation analysis
Bull/base/bear scenarios
Thesis + antithesis
Missing information
Conflicting information

Evidence

PDF filing ingestion
Hybrid retrieval
Reranking
Source provenance
Claim → evidence mapping
Citations
Evidence sufficiency detection

Research workflow

Research question
Task decomposition
Retrieval
Gap detection
Bounded follow-up research
Evidence reconciliation
Structured report
Persisted research state

Infrastructure

FastAPI
PostgreSQL + pgvector
BM25
Redis
API worker
Streamlit
Caddy
MCP tool layer

Evaluation

40-question benchmark
Retrieval metrics
Answer metrics
Unanswerable questions
Poisoned documents
A/B experiments
Regression dataset
7. DEFERRED

You should actually have things in this section.

I'd put:

Authentication
Multi-user accounts
Multi-tenancy
Portfolio tracking
Real-time market monitoring
Autonomous trading
Buy/sell execution
Broker integration
Personalized investment advice
Continuous autonomous research
Mobile application
Multiple document formats
Large-scale distributed workers
Kafka/Celery
Fine-tuning
Complex agent memory
Real-time streaming research
Automated investment recommendations

This is important because scope control is part of the engineering skill you're trying to practice.