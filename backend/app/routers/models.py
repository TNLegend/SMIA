# app/routers/models.py
import shutil, zipfile, shlex, subprocess
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import get_current_user, User
from app.db import SessionLocal
from app.models import AIProject, ModelRun

router = APIRouter(prefix="/projects/{project_id}/model", tags=["model"])
REQUIRED_FILES = {"train.py", "config.yaml", "requirements.txt", "model.py"}

def get_session():
    with SessionLocal() as sess:
        yield sess

@router.post("/upload", status_code=200)
async def upload_model_code(
    project_id: int,
    zip_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projet introuvable")
    if proj.owner != current_user.username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès interdit")

    tmp = NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        tmp.write(await zip_file.read()); tmp.flush()
        with zipfile.ZipFile(tmp.name) as z:
            root = {Path(f).name for f in z.namelist() if "/" not in f.strip("/")}
            missing = REQUIRED_FILES - root
            if missing:
                return JSONResponse(400, {"ok": False, "missing": list(missing)})
            dest = Path(__file__).resolve().parents[2] / "storage/models" / f"project_{project_id}"
            if dest.exists(): shutil.rmtree(dest)
            dest.mkdir(parents=True)
            z.extractall(dest)
    finally:
        tmp.close()
        Path(tmp.name).unlink(missing_ok=True)

    return {"ok": True, "files": [p.name for p in dest.iterdir()]}


class TrainRequest(BaseModel):
    train_data_path: str


@router.post("/train", status_code=202)
def launch_training(
    project_id: int,
    payload: TrainRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj or proj.owner != current_user.username:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    run = ModelRun(project_id=project_id, status="pending")
    sess.add(run); sess.commit(); sess.refresh(run)
    background_tasks.add_task(_do_training, project_id, run.id, payload.train_data_path)
    return {"run_id": run.id, "status": run.status}


def _do_training(project_id: int, run_id: int, train_data_path: str):
    with SessionLocal() as sess:
        run = sess.get(ModelRun, run_id)
        run.started_at, run.status = datetime.utcnow(), "running"
        sess.add(run); sess.commit()

        base = Path(__file__).resolve().parents[2] / "storage/models" / f"project_{project_id}"
        out = base / "output"; out.mkdir(exist_ok=True)
        cmd = (
            f"docker run --rm "
            f"-v {base}:/code "
            f"-v {train_data_path}:/data/train.csv "
            f"-v {out}:/output "
            f"my-ml-runtime bash -c "
            f"\"pip install -r /code/requirements.txt && "
            f"python /code/train.py --data /data/train.csv "
            f"--config /code/config.yaml --out /output\""
        )
        proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        logs = "".join(proc.stdout or [])
        ret = proc.wait()

        run = sess.get(ModelRun, run_id)
        run.finished_at = datetime.utcnow()
        run.logs, run.status = logs, ("succeeded" if ret == 0 else "failed")
        sess.add(run); sess.commit()


@router.get("/runs", response_model=List[ModelRun])
def list_runs(
    project_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    proj = sess.get(AIProject, project_id)
    if not proj: raise HTTPException(404, "Projet introuvable")
    return sess.exec(select(ModelRun).where(ModelRun.project_id == project_id)).all()


@router.get("/runs/{run_id}", response_model=ModelRun)
def get_run(
    project_id: int,
    run_id: int,
    current_user: User = Depends(get_current_user),
    sess: Session = Depends(get_session),
):
    run = sess.get(ModelRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Run introuvable")
    return run