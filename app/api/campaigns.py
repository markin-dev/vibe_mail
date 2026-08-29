"""Роутер кампаний и связанных с ними операций."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import CampaignStatus
from app.schemas.campaign import CampaignRead, CreateCampaign, MessageOut
from app.schemas.envelope import (
    CampaignReadEnvelope,
    ImportPreviewEnvelope,
    ImportResultEnvelope,
    ListCampaignReadEnvelope,
    ListRecipientReadEnvelope,
    MessageOutEnvelope,
    ok,
)
from app.schemas.import_recipients import RecipientsImportText
from app.schemas.recipient import RecipientsBulk
from app.services import campaign_service as cs
from app.services import config_service as cfs
from app.services import import_service as imp
from app.services import recipient_service as rs

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CampaignReadEnvelope)
def create_campaign(data: CreateCampaign, db: Session = Depends(get_db)):
    return ok(cs.create_campaign(db, data))


@router.get("", response_model=ListCampaignReadEnvelope)
def list_campaigns(db: Session = Depends(get_db)):
    result = []
    for camp in cs.list_campaigns(db):
        item = CampaignRead.model_validate(camp)
        item.totals = cs.get_progress(db, camp)
        result.append(item)
    return ok(result)


@router.get("/{campaign_id}", response_model=CampaignReadEnvelope)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    camp = cs.get_campaign(db, campaign_id)
    item = CampaignRead.model_validate(camp)
    item.totals = cs.get_progress(db, camp)
    return ok(item)


@router.post(
    "/{campaign_id}/recipients",
    status_code=status.HTTP_201_CREATED,
    response_model=ListRecipientReadEnvelope,
)
def add_recipients(campaign_id: int, payload: RecipientsBulk, db: Session = Depends(get_db)):
    cs.get_campaign(db, campaign_id)  # 404, если кампании нет
    return ok(rs.add_recipients(db, campaign_id, payload.items))


@router.get("/{campaign_id}/recipients", response_model=ListRecipientReadEnvelope)
def list_recipients(campaign_id: int, db: Session = Depends(get_db)):
    cs.get_campaign(db, campaign_id)
    return ok(rs.get_recipients(db, campaign_id))


@router.post(
    "/{campaign_id}/recipients/preview",
    response_model=ImportPreviewEnvelope,
)
def preview_recipients_import(
    campaign_id: int, payload: RecipientsImportText, db: Session = Depends(get_db)
):
    cs.get_campaign(db, campaign_id)
    return ok(imp.build_preview(db, campaign_id, payload.text))


@router.post(
    "/{campaign_id}/recipients/import",
    status_code=status.HTTP_201_CREATED,
    response_model=ImportResultEnvelope,
)
def import_recipients(
    campaign_id: int, payload: RecipientsImportText, db: Session = Depends(get_db)
):
    cs.get_campaign(db, campaign_id)
    return ok(imp.import_recipients(db, campaign_id, payload.text))


@router.post(
    "/{campaign_id}/configs/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MessageOutEnvelope,
)
def generate_configs(campaign_id: int, db: Session = Depends(get_db)):
    """Ставит в очередь конфиги без файла — генерацию делает фоновый воркер."""
    camp = cs.get_campaign(db, campaign_id)
    queued = cfs.enqueue_campaign_configs(db, camp.id)

    return ok(MessageOut(detail=f"В очереди на генерацию: {queued}", campaign_id=camp.id))


@router.post(
    "/{campaign_id}/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MessageOutEnvelope,
)
def start_campaign(campaign_id: int, db: Session = Depends(get_db)):
    camp = cs.get_campaign(db, campaign_id)
    problems = rs.validate_campaign_ready(db, camp)
    if problems:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": problems})
    cs.set_status(db, camp, CampaignStatus.IN_PROGRESS)
    return ok(MessageOut(detail="Рассылка запущена", campaign_id=camp.id))


@router.post("/{campaign_id}/stop", response_model=MessageOutEnvelope)
def stop_campaign(campaign_id: int, db: Session = Depends(get_db)):
    camp = cs.get_campaign(db, campaign_id)
    cs.set_status(db, camp, CampaignStatus.NEW)
    return ok(MessageOut(detail="Рассылка остановлена", campaign_id=camp.id))


@router.delete("/{campaign_id}", response_model=MessageOutEnvelope)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    cs.delete_campaign(db, campaign_id)
    return ok(MessageOut(detail="Кампания удалена", campaign_id=campaign_id))
