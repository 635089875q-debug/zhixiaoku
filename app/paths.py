import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = Path(
    os.getenv(
        "DATA_PATH",
        str(PROJECT_ROOT / "data")
    )
).resolve()

DOCUMENTS_PATH = DATA_PATH / "documents"
INDEX_DIRECTORY = DATA_PATH / "index"
INDEX_PATH = INDEX_DIRECTORY / "knowledge_new.index"
CHUNKS_PATH = INDEX_DIRECTORY / "chunks_new.json"
STATIC_PATH = PROJECT_ROOT / "app" / "static"
