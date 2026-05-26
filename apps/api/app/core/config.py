import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
ROOT_ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ROOT_ENV_PATH)

DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))
LOG_DIR = Path(os.getenv("LOG_DIR", Path(__file__).resolve().parent.parent / "logs"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "db.json"

# LLM config
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai_compatible")
DEFAULT_LLM_BASE_URL = os.getenv("DEFAULT_LLM_BASE_URL", "")
DEFAULT_LLM_API_KEY = os.getenv("DEFAULT_LLM_API_KEY", "")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "")
DEFAULT_LLM_TIMEOUT_SECONDS = float(os.getenv("DEFAULT_LLM_TIMEOUT_SECONDS", "12"))

RESUME_ANALYZER_MODEL = os.getenv("RESUME_ANALYZER_MODEL", "")
JOB_ANALYZER_MODEL = os.getenv("JOB_ANALYZER_MODEL", "")
QUESTION_ROUTER_MODEL = os.getenv("QUESTION_ROUTER_MODEL", "")
INTERVIEWER_MODEL = os.getenv("INTERVIEWER_MODEL", "")
ASSESSMENT_MODEL = os.getenv("ASSESSMENT_MODEL", "")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai_compatible")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() in {"1", "true", "yes"}

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
