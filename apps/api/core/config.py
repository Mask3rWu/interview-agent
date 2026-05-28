import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
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
RESUME_ANALYZER_LLM_BACKEND = os.getenv("RESUME_ANALYZER_LLM_BACKEND", "text")
JOB_ANALYZER_LLM_BACKEND = os.getenv("JOB_ANALYZER_LLM_BACKEND", "text")
QUESTION_ROUTER_LLM_BACKEND = os.getenv("QUESTION_ROUTER_LLM_BACKEND", "text")
INTERVIEWER_LLM_BACKEND = os.getenv("INTERVIEWER_LLM_BACKEND", "text")
ASSESSMENT_LLM_BACKEND = os.getenv("ASSESSMENT_LLM_BACKEND", "text")

MLLM_BASE_URL = os.getenv("MLLM_BASE_URL", "")
MLLM_API_KEY = os.getenv("MLLM_API_KEY", "")
MLLM_MODEL = os.getenv("MLLM_MODEL", "")
MLLM_TIMEOUT_SECONDS = float(os.getenv("MLLM_TIMEOUT_SECONDS", "60"))
PDF_VISION_AGENT_MODEL = os.getenv("PDF_VISION_AGENT_MODEL", "")
PDF_IMAGE_DPI = int(os.getenv("PDF_IMAGE_DPI", "160"))
PDF_MAX_PAGES = int(os.getenv("PDF_MAX_PAGES", "200"))
PDF_MAX_IMAGES_PER_PAGE = int(os.getenv("PDF_MAX_IMAGES_PER_PAGE", "20"))
PDF_IMAGE_CONCURRENCY = int(os.getenv("PDF_IMAGE_CONCURRENCY", "4"))

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
