"""PrintMind 全局配置与常量。"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "printmind.db"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# PETG 参数合理范围（超出返回 422）
PARAM_RANGES = {
    "nozzle_temp": (180, 300),
    "bed_temp": (20, 120),
    "print_speed": (1, 500),
    "fan_speed": (0, 100),
    "layer_height": (0.05, 0.5),
    "retraction": (0, 10),
}
