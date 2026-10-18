# Project data

This directory separates data by ownership and reproducibility.

```text
data/
├── README.md
├── watsonx_docs_qa_manifest.json  # Pinned source revision and local hashes
├── raw/                           # Downloaded third-party data; ignored by Git
├── synthetic/                     # Project-owned demo company documents
└── evaluation/                    # Questions, expected sources, and access outcomes
```

## External raw data

The initial retrieval corpus is IBM's Apache-2.0-licensed `watsonxDocsQA` dataset. Download it with:

```bash
.venv/bin/python -m pip install '.[data]'
.venv/bin/python scripts/download_watsonx_docs_qa.py
```

The script downloads a pinned Hugging Face revision to:

```text
data/raw/watsonx_docs_qa/
```

Raw third-party files are deliberately excluded from Git. The committed manifest records their source revision, size, and SHA-256 hashes so the local corpus remains reproducible and verifiable.

Before redistributing any external data, review its current dataset card, source terms, and attribution requirements.

The pinned snapshot contains 1,144 corpus documents and 75 question-answer examples split into 45 training and 30 test examples.

## Project-owned data

Our synthetic HR, Finance, Engineering, intern-onboarding, and general-company documents will be stored in `data/synthetic/` and committed to Git. They will contain no real personal, payroll, customer, or company-confidential information.

