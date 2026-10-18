"""Download the pinned watsonxDocsQA snapshot and record local file hashes."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from huggingface_hub import snapshot_download


DATASET_ID = "ibm-research/watsonxDocsQA"
DATASET_REVISION = "f7da4b6d8a8c4609c49fda06af3bea29b6ef9be4"
DATASET_LICENSE = "Apache-2.0"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "watsonx_docs_qa"
MANIFEST_PATH = PROJECT_ROOT / "data" / "watsonx_docs_qa_manifest.json"


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of one downloaded file."""

    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for block in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def downloaded_files() -> List[Dict[str, object]]:
    """Describe user-facing snapshot files while ignoring downloader metadata."""

    records: List[Dict[str, object]] = []
    for path in sorted(DOWNLOAD_DIRECTORY.rglob("*")):
        if not path.is_file() or ".cache" in path.parts:
            continue
        records.append(
            {
                "path": str(path.relative_to(DOWNLOAD_DIRECTORY)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return records


def main() -> None:
    """Download one immutable dataset revision and write its provenance manifest."""

    DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=DATASET_ID,
        repo_type="dataset",
        revision=DATASET_REVISION,
        local_dir=DOWNLOAD_DIRECTORY,
    )

    files = downloaded_files()
    manifest = {
        "dataset_id": DATASET_ID,
        "source_url": f"https://huggingface.co/datasets/{DATASET_ID}",
        "revision": DATASET_REVISION,
        "license": DATASET_LICENSE,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "local_directory": "data/raw/watsonx_docs_qa",
        "file_count": len(files),
        "total_size_bytes": sum(int(record["size_bytes"]) for record in files),
        "files": files,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(
        f"Downloaded {manifest['file_count']} files "
        f"({manifest['total_size_bytes']} bytes) to {DOWNLOAD_DIRECTORY}"
    )
    print(f"Wrote provenance manifest to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()

