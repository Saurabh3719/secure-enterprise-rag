# Secure Enterprise RAG

A learning-first, production-minded Retrieval-Augmented Generation (RAG) system for answering questions over internal company documents while enforcing role-based access control (RBAC), evidence-based answers, citations, and security guardrails.

> **Current status:** Milestone 1 — authentication and default-deny RBAC foundation.

> **Selected retrieval dataset:** IBM `watsonxDocsQA`, pinned locally through a reproducible download script. Project-specific RBAC metadata and sensitive-looking examples will be synthetic.

## Why this project exists

A basic RAG demo retrieves text and sends it to a language model. An enterprise system must also answer harder questions:

- Is this user allowed to retrieve this document?
- Can a malicious document manipulate the model?
- What happens when no trustworthy evidence is found?
- Can every answer be traced to its sources?
- Can we measure retrieval quality, leakage, latency, and cost?

This project will build those capabilities one layer at a time. The documentation records not only *what* we build, but *why*, how files and functions connect, common failures, rejected alternatives, and interview-ready explanations.

## First objective: security foundation

Before using an LLM, we will create a minimal permission-aware retrieval contract.

**Goal:** Given a user and a document, the system must deterministically decide whether the user may retrieve that document.

The first milestone will define:

1. Users and identities
2. The five initial roles: `intern`, `engineer`, `hr`, `finance`, and `admin`
3. Document classifications
4. Access-control metadata attached to every document chunk
5. Default-deny authorization rules
6. Tests proving that unauthorized content is never returned

**Acceptance example**

```text
User:     engineer@example.com
Role:     engineer
Question: "What are the executive salary bands?"

Expected retrieval result: zero HR/Finance-restricted chunks
Expected response: safe refusal or access-request guidance
Expected audit event: authorization denial recorded without exposing document text
```

This comes first because an LLM instruction such as “do not reveal confidential information” is not a security boundary. Unauthorized text must be filtered out before it reaches the model.

### Authentication versus authorization

```mermaid
flowchart LR
    A[Login ID + password] --> B[Authentication service]
    B -->|valid credentials| C[User identity: login ID + role]
    B -->|invalid credentials| D[Generic login failure]
    C --> E[Authorization policy]
    F[Chunk ACL: allowed roles] --> E
    E -->|allow| G[Chunk may enter retrieval results]
    E -->|deny by default| H[Chunk is removed]
```

- **Authentication** proves who the user is by checking the login ID and password.
- **Authorization** checks what the authenticated role is permitted to access.
- The password is never stored. The implementation stores a unique salted Argon2id hash.
- The authenticated `UserIdentity` contains only the normalized login ID, role, and active status—not the password hash.
- Missing, inactive, and wrong-password attempts all perform password verification and return the same result, reducing login-ID enumeration through messages and timing.
- An empty chunk ACL denies access. `admin` is the only initial role with an explicit global override.

## System overview

```mermaid
flowchart LR
    subgraph Offline[Offline ingestion]
        A[Company documents] --> B[Parse and clean]
        B --> C[Split into chunks]
        C --> D[Attach metadata and ACL]
        D --> E1[Vector index]
        D --> E2[Keyword index]
    end

    subgraph Online[Online question answering]
        U[Authenticated user] --> P[RBAC policy filter]
        Q[Question] --> P
        P --> H[Hybrid retrieval]
        E1 --> H
        E2 --> H
        H --> R[Re-ranker]
        R --> G[Guarded LLM]
        G --> O[Answer with citations or abstention]
    end

    P --> L[Audit log]
    O --> L
    O --> V[Evaluation and monitoring]
```

## The two pipelines

### 1. Ingestion pipeline

The ingestion pipeline runs when documents are added or changed.

```text
Source → parser → cleaner → chunker → metadata/ACL enrichment → embeddings → indexes
```

- A **parser** extracts text and structure from files such as PDFs or Markdown.
- A **chunker** divides a large document into passages small enough to retrieve and send to a model.
- **Metadata** describes a chunk: source, owner, department, version, and classification.
- An **ACL** (Access Control List) states which users, roles, or groups may access it.
- An **embedding** is a numeric representation used for similarity search.
- The **vector index** supports meaning-based search.
- The **keyword index** preserves exact matches such as names, product codes, and error IDs.

### 2. Query pipeline

The query pipeline runs for every user question.

```text
Identity → authorization filter → hybrid search → re-ranking → context building
         → guarded generation → citation validation → response → audit/evaluation
```

The authorization filter is applied during retrieval—not after generation—so forbidden chunks never enter the model context.

## Planned layers

| Milestone | Layer | Learning outcome | Deliverable |
|---:|---|---|---|
| 0 | Architecture | Understand the complete system and threat boundaries | This README and decision log |
| 1 | RBAC foundation | Model users, roles, documents, and default-deny policies | Authorization module and tests |
| 2 | Ingestion | Parse, clean, chunk, and enrich documents | Repeatable ingestion pipeline |
| 3 | Search | Compare vector, keyword, and hybrid retrieval | Permission-aware retriever |
| 4 | Re-ranking | Improve the ordering of retrieved evidence | Re-ranker with measurable gains |
| 5 | Generation | Produce grounded answers with citations | RAG answer service |
| 6 | Guardrails | Resist injection, leakage, and unsupported answers | Input, retrieval, and output checks |
| 7 | Evaluation | Measure retrieval and answer quality | Automated evaluation dataset and report |
| 8 | API and UI | Expose the system safely to users | Authenticated API and small client |
| 9 | Operations | Make the system reproducible and observable | Docker Compose, logs, metrics, CI |
| 10 | Deployment | Demonstrate a production path | Cloud deployment; Kubernetes optional |

## Technology decision status

No major library is considered “used” until it appears in working, tested code.

| Area | Current decision | Why |
|---|---|---|
| Language | Python 3.9+ (in use) | Strong ecosystem for RAG, evaluation, APIs, and data processing |
| Password hashing | `argon2-cffi` / Argon2id (in use) | OWASP-preferred memory-hard password hashing with a unique random salt |
| API | FastAPI (planned) | Typed request models, OpenAPI documentation, and async support |
| Relational data | PostgreSQL (planned) | Users, roles, document metadata, and audit records need relational integrity |
| Vector search | Qdrant or PostgreSQL/pgvector (evaluation pending) | Both support metadata filtering needed for RBAC |
| Keyword search | OpenSearch or PostgreSQL full-text search (evaluation pending) | Choice depends on operational complexity and retrieval quality |
| RAG orchestration | Direct Python first; LangChain or LlamaIndex only if justified | Learning core mechanics prevents framework abstractions from hiding the pipeline |
| Guardrails | Custom deterministic checks first; NeMo Guardrails evaluation later | Authorization must remain application logic, not prompt logic |
| Evaluation | Ragas plus custom security tests (planned) | Generic RAG metrics do not prove permission isolation |
| Local infrastructure | Docker Compose (planned) | Reproducible databases and services with low setup cost |
| Cluster orchestration | Kubernetes excluded from early milestones | It adds deployment complexity before product behavior is proven |
| Initial retrieval corpus | IBM `watsonxDocsQA` (downloaded locally) | Apache-2.0 corpus with 1,144 documents and 75 gold QA examples |

## Included and deliberately excluded

### Included in the core build

- RBAC and document-level/chunk-level authorization
- Hybrid retrieval and re-ranking
- Grounded answers with citations and abstention
- Prompt-injection and data-leakage defenses
- Audit logging without sensitive-content leakage
- Automated retrieval, generation, and security evaluation
- Docker-based reproducible local development

### Excluded initially

- **Kubernetes:** useful at scale, but unnecessary before one deployable service works.
- **Fine-tuning:** RAG should solve changing private knowledge without retraining the model.
- **Autonomous agents:** tool-using agents enlarge the attack surface and are not required for the initial knowledge assistant.
- **Many document formats:** we will make one or two formats reliable before adding connectors.
- **Framework-heavy abstractions:** we will implement the smallest clear pipeline before adopting LangChain or LlamaIndex.

Exclusion does not always mean permanent rejection. It means the technology does not yet solve a demonstrated requirement.

## Planned repository structure

```text
secure-enterprise-rag/
├── README.md                    # Living project guide and build history
├── docs/                        # Deeper concepts, decisions, and troubleshooting
├── src/
│   └── secure_rag/
│       ├── auth/
│       │   ├── models.py        # Roles, stored users, safe identities, chunks
│       │   ├── passwords.py     # Salted password hashing and verification
│       │   ├── service.py       # Registration and login orchestration
│       │   └── policy.py        # Default-deny chunk authorization
│       ├── ingestion/           # Parsing, cleaning, chunking, metadata
│       ├── retrieval/           # Vector, keyword, hybrid search, re-ranking
│       ├── generation/          # Context assembly, prompts, citations
│       ├── guardrails/          # Injection, leakage, and output checks
│       ├── evaluation/          # Quality and security metrics
│       └── api/                 # HTTP endpoints and dependency wiring
├── tests/                       # Unit, integration, security, and evaluation tests
├── data/
│   ├── raw/                     # Local third-party downloads; never committed
│   ├── synthetic/               # Project-owned role-specific demo documents
│   └── evaluation/              # Questions and expected retrieval/access outcomes
├── scripts/                     # Reproducible dataset and maintenance commands
└── docker-compose.yml           # Local infrastructure (added later)
```

## How future functions will connect

Names below describe the intended interfaces; they are not implemented yet.

```mermaid
sequenceDiagram
    actor User
    participant API
    participant Identity as Identity service
    participant Policy as authorize()
    participant Search as retrieve_authorized()
    participant Rank as rerank()
    participant LLM as generate_grounded_answer()
    participant Guard as validate_response()
    participant Audit as record_event()

    User->>API: Ask question + authentication token
    API->>Identity: resolve_identity(token)
    Identity-->>API: user_id, roles, groups
    API->>Policy: build_access_filter(identity)
    Policy-->>API: enforceable metadata filter
    API->>Search: retrieve_authorized(question, filter)
    Search-->>API: permitted candidate chunks
    API->>Rank: rerank(question, candidates)
    Rank-->>API: ordered evidence
    API->>LLM: generate_grounded_answer(question, evidence)
    LLM-->>API: answer + citations
    API->>Guard: validate_response(answer, evidence)
    Guard-->>API: approved, refused, or abstained response
    API->>Audit: record_event(identity, sources, decision)
    API-->>User: Safe response
```

Each implementation milestone will replace these planned names with links to the actual files, functions, tests, inputs, outputs, and failure behavior.

### Implemented authentication/RBAC call graph

```mermaid
flowchart TD
    Register[AuthenticationService.register] --> Normalize[normalize_login_id]
    Register --> Hash[hash_password]
    Hash --> Argon[Argon2id + random salt]
    Register --> Repo[InMemoryUserRepository]

    Login[AuthenticationService.authenticate] --> Repo
    Login --> Verify[verify_password]
    Verify --> Compare[hmac.compare_digest]
    Login --> Identity[UserIdentity]

    Identity --> Access[can_access]
    Chunk[DocumentChunk.allowed_roles] --> Access
    Access --> Filter[filter_authorized_chunks]
    Filter --> Safe[Authorized chunks only]
```

The in-memory repository is intentionally temporary. PostgreSQL will later replace it without changing the authentication service's responsibility.

## Failure-oriented learning checklist

When RAG “does not work,” identify the failing layer instead of immediately changing the prompt.

| Symptom | Likely layer | Example causes |
|---|---|---|
| No documents found | Ingestion/indexing | Missing source, parsing failure, stale index |
| Relevant document exists but is not retrieved | Retrieval | Poor chunks, weak embedding, vocabulary mismatch, threshold too strict |
| Correct chunk appears too low | Ranking | Weak fusion weights or re-ranker |
| Authorized user sees nothing | Authorization | Incorrect role mapping or metadata filter |
| Unauthorized user sees a sensitive chunk | Security-critical authorization failure | Missing ACL, filter bypass, unsafe cache key |
| Evidence is correct but answer is wrong | Generation | Bad context construction, ambiguous prompt, model limitation |
| Answer invents unsupported facts | Grounding/guardrails | No abstention rule or citation validation |
| Good answer is slow or expensive | Operations | Excessive candidates, oversized chunks, repeated embeddings |

## Build journal

### 2026-10-18 — Repository initialization

- Cloned the empty GitHub repository.
- Defined the project purpose and security-first architecture.
- Selected permission modeling as the first implementation objective.
- Documented planned technologies without claiming they are already implemented.
- Deferred Kubernetes, fine-tuning, autonomous agents, and premature framework adoption.

### 2026-10-18 — Authentication and role model

- Added the roles `intern`, `engineer`, `hr`, `finance`, and `admin`.
- Added login-ID normalization, account registration, and password authentication.
- Stored salted Argon2id hashes instead of plaintext passwords.
- Separated stored `UserRecord` data from the safe `UserIdentity` passed to authorization.
- Added default-deny chunk ACL filtering and an explicit administrator override.
- Used an in-memory user repository for this isolated milestone; PostgreSQL remains deferred.
- Added unit tests for login behavior, salt uniqueness, wrong passwords, cross-role denial, inactive users, and unauthorized-chunk filtering.
- Added dummy password verification for missing and inactive accounts so invalid-login paths have more similar timing.
- Replaced an initial `hashlib.scrypt` implementation after tests showed that the local Python/OpenSSL build did not expose `scrypt`. Keeping the failed assumption documented explains why `argon2-cffi` became the first runtime dependency.

### 2026-10-18 — Retrieval dataset selection

- Selected IBM `watsonxDocsQA` as the initial external retrieval corpus because it is small enough to inspect and includes gold document IDs and answers.
- Pinned the Hugging Face snapshot to commit `f7da4b6d8a8c4609c49fda06af3bea29b6ef9be4`.
- Added a reproducible downloader and a checksum manifest.
- Downloaded and verified five snapshot files locally (6,092,305 bytes): 1,144 corpus documents plus 45 training and 30 test questions.
- Kept third-party raw files local and out of Git; only provenance metadata and project-owned synthetic documents are committed.
- Deferred EnterpriseRAG-Bench because its 500,000+ documents would add cost and debugging complexity before the small pipeline works.

## Download the retrieval dataset

```bash
.venv/bin/python -m pip install '.[data]'
.venv/bin/python scripts/download_watsonx_docs_qa.py
```

The raw snapshot is stored locally at `data/raw/watsonx_docs_qa/` and is ignored by Git. `data/watsonx_docs_qa_manifest.json` records its pinned revision and file hashes.

## Run the current tests

Create a virtual environment, install the package, and run the tests:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m unittest discover -s tests -v
```

## Documentation rule

Every meaningful implementation should update this README or a linked document with:

1. What changed
2. Why it was needed
3. Libraries introduced and why
4. Alternatives rejected or deferred
5. File/function connections
6. Tests performed
7. Known failure modes and troubleshooting steps

This keeps the repository useful as both a working project and an interview study guide.

