"""Роутер кампаний и связанных с ними операций."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_worker
from app.db.models import CampaignStatus
from app.schemas.campaign import (
    CampaignCreate,
    CampaignRead,
    ImportCsvResult,
    MessageOut,
)
from app.schemas.envelope import (
    CampaignReadEnvelope,
    ImportCsvResultEnvelope,
    ListCampaignReadEnvelope,
    ListRecipientReadEnvelope,
    MessageOutEnvelope,
    ok,
)
from app.schemas.recipient import RecipientCreate, RecipientRead, RecipientsBulk
from app.services import campaign_service as cs
from app.services import recipient_service as rs
from app.services.worker import Worker

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CampaignReadEnvelope)
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
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


@router.post("/{campaign_id}/import-csv", response_model=ImportCsvResultEnvelope)
async def import_csv(
    campaign_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    cs.get_campaign(db, campaign_id)
    content = await file.read()
    return ok(ImportCsvResult(**cs.import_csv(db, campaign_id, content)))


@router.post(
    "/{campaign_id}/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MessageOutEnvelope,
)
def start_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    worker: Worker = Depends(get_worker),
):
    camp = cs.get_campaign(db, campaign_id)
    problems = rs.validate_campaign_ready(db, camp)
    if problems:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": problems})
    cs.set_status(db, camp, CampaignStatus.RUNNING)
    return ok(MessageOut(detail="Рассылка запущена", campaign_id=camp.id))


@router.post("/{campaign_id}/stop", response_model=MessageOutEnvelope)
def stop_campaign(campaign_id: int, db: Session = Depends(get_db)):
    camp = cs.get_campaign(db, campaign_id)
    cs.set_status(db, camp, CampaignStatus.PAUSED)
    return ok(MessageOut(detail="Рассылка приостановлена", campaign_id=camp.id))
