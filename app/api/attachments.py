"""Роутер загрузки вложений получателям."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.envelope import AttachmentReadEnvelope, ok
from app.services import campaign_service as cs
from app.services import recipient_service as rs

router = APIRouter(prefix="/api/campaigns", tags=["attachments"])


@router.post(
    "/{campaign_id}/recipients/{recipient_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentReadEnvelope,
)
async def upload_attachment(
    campaign_id: int,
    recipient_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    cs.get_campaign(db, campaign_id)
    recipient = rs.get_recipient(db, recipient_id)
    if recipient.campaign_id != campaign_id:
        raise HTTPException(
            status_code=400, detail="Получатель не относится к кампании"
        )
    content = await file.read()
    return ok(rs.add_attachment(db, recipient, file.filename or "file", content))
