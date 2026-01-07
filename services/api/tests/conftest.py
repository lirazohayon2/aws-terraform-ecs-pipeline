import sys
from pathlib import Path

# Add services/api to PYTHONPATH so "app" is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
