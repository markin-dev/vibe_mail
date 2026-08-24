"""Роутер получателей (удаление)."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import recipient_service as rs

router = APIRouter(prefix="/api/recipients", tags=["recipients"])


@router.delete("/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipient(recipient_id: int, db: Session = Depends(get_db)):
    recipient = rs.get_recipient(db, recipient_id)
    db.delete(recipient)
    db.commit()
