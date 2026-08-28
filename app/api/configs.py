"""Роутер конфигов (скачивание файла)."""
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import config_service as cfs

router = APIRouter(prefix="/api/configs", tags=["configs"])


@router.get("/{config_id}/download")
def download_config(config_id: int, db: Session = Depends(get_db)):
    """Отдаёт файл конфига. Ответ бинарный, без обёртки ApiEnvelope."""
    config = cfs.get_config(db, config_id)
    if config.content is None:
        raise HTTPException(status_code=404, detail="Файл конфига ещё не сгенерирован")

    filename = config.filename or f"{config.name}.conf"

    return Response(
        content=config.content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
        },
    )
