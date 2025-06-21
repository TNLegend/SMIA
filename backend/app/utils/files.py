# app/utils/files.py
import shutil
from pathlib import Path

def purge_project_storage(project_id: int) -> None:
    root = Path(__file__).resolve().parents[2] / "storage"

    models_dir = root / "models" / f"project_{project_id}"
    data_dir   = root / "data"   / f"project_{project_id}"

    for d in (models_dir, data_dir):
        try:
            shutil.rmtree(d)
        except FileNotFoundError:
            pass
