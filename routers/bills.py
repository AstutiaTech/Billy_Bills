from fastapi import APIRouter, Depends
from schemas import ResponseDataMoreModel, ResponseModel, BillerCategoryModel, BillerServiceModel, ValidateBillerModel, PayBillModel
from typing import List
from modules.main.billers import retrieve_bill_category, retrieve_bill_category_services, validate_service_neo, pay_bill, process_transaction_status
from database.db import get_session
from sqlalchemy.orm import Session
router = APIRouter()

@router.get("/categories", response_model=List[BillerCategoryModel])
async def categories(db: Session = Depends(get_session)):
    return retrieve_bill_category(db=db)
    
@router.get("/services_by_category/{category_id}", response_model=List[BillerServiceModel])
async def service_by_category(db: Session = Depends(get_session), category_id: int=0):
    return retrieve_bill_category_services(db=db, category_id=category_id)

@router.post("/validate", response_model=ResponseDataMoreModel)
async def validate(fields: ValidateBillerModel, db: Session = Depends(get_session)):
    return validate_service_neo(db=db, service_code=fields.service_code, customer=fields.customer)
    
@router.post("/pay", response_model=ResponseDataMoreModel)
async def pay(fields: PayBillModel, db: Session = Depends(get_session)):
    return pay_bill(db=db, service_code=fields.service_code, customer_id=fields.customer_id, branch_id=fields.branch_id, channel_id=fields.channel_id, nuban=fields.nuban, biller_customer=fields.customer, ip_address=fields.ip_address)
    
@router.get("/status/{reference}", response_model=ResponseDataMoreModel)
async def service_status(db: Session = Depends(get_session), reference: str=None):
    return process_transaction_status(db=db, reference=reference)