from database.model import get_all_categories, get_services_by_category, create_transaction, update_transaction, get_service_by_code, get_transaction_by_reference
from models.services import get_service_by_id
from modules.utils.req import validate_bill_service, make_bill_payment, get_bill_transaction_status
from modules.utils.tools import generate_external_ref
from modules.external.account import get_account_by_account_number, fund_transfer_debit_customer_account_external
from modules.external.settings import get_TSS_bill, get_TSS_bill_fee
from modules.external.customer import get_customer_info_by_id
from modules.external.transaction import approve_transaction, cancel_transaction
from sqlalchemy.orm import Session
from datetime import date

def retrieve_bill_category(db: Session):
    data = get_all_categories(db=db)
    categories = []
    if len(data) > 0:
        for i in range(len(data)):
            category = data[i]
            mer = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'category_code': category.category_code,
            }
            categories.append(mer)
    return categories

def retrieve_bill_category_services(db: Session, category_id: int=0):
    data = get_services_by_category(db=db, category_id=category_id)
    services = []
    if len(data) > 0:
        for i in range(len(data)):
            service = data[i]
            mer = {
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'label_name': service.label_name,
                'service_code': service.service_code,
                'amount': service.amount,
                'fee': service.fee,
                'is_flat': service.is_flat,
                'min_amount': service.min_amount,
                'max_amount': service.max_amount,
            }
            services.append(mer)
    return services

def validate_service(item_code=None, code=None, customer=None):
    resp = validate_bill_service(item_code=item_code, code=code, customer=customer)
    if resp is None:
        return {
            'status': False,
            'message': 'Unknown Failure',
            'data': {}
        }
    else:
        if 'status' not in resp:
            return {
                'status': False,
                'message': 'Unknown Failure',
                'data': {}
            }
        else:
            if resp['status'] != "success":
                return {
                    'status': False,
                    'message': 'Validation failed',
                    'data': {}
                }
            else:
                if 'data' not in resp:
                    return {
                        'status': False,
                        'message': 'Unknown Failure',
                        'data': {}
                    }
                else:
                    response_data = resp['data']
                    data = {
                        'customer_name': response_data['name'],
                        'customer_id': customer,
                    }
                    return {
                        'status': True,
                        'message': 'Success',
                        'data': data,
                    }

def validate_service_neo(db: Session, service_code: str=None, customer: str=None):
    service = get_service_by_code(db=db, code=service_code)
    if service is None:
        return {
            'status': False,
            'message': 'Service not found',
            'data': {},
        }
    else:
        if service.provider_id == 1:
            resp = validate_bill_service(item_code=service.fw_item_code, code=service.fw_biller_code, customer=customer)
            if resp is None:
                return {
                    'status': False,
                    'message': 'Unknown Failure',
                    'data': {},
                }
            else:
                if 'status' not in resp:
                    return {
                        'status': False,
                        'message': 'Unknown Failure',
                        'data': {}
                    }
                else:
                    if resp['status'] != "success":
                        return {
                            'status': False,
                            'message': 'Validation failed',
                            'data': {}
                        }
                    else:
                        if 'data' not in resp:
                            return {
                                'status': False,
                                'message': 'Unknown Failure',
                                'data': {}
                            }
                        else:
                            response_data = resp['data']
                            data = {
                                'customer_name': response_data['name'],
                                'customer_id': customer,
                            }
                            return {
                                'status': True,
                                'message': 'Success',
                                'data': data,
                            }
        else:
            return {
                'status': False,
                'message': 'Service Unavailable',
                'data': {},
            }

def process_service_payment(db: Session, service_id: int=0, amount: float=0, reference: str=None, biller_name: str=None, customer: str=None):
    service = get_service_by_id(db=db, id=service_id)
    if service is None:
        return {
            'status': False,
            'message': 'Service not found',
            'data': {},
        }
    else:
        if service.provider_id == 1:
            req = make_bill_payment(customer=customer, amount=amount, payment_type=biller_name, biller_name=biller_name, reference=reference)
            if req is None:
                return {
                    'status': False,
                    'message': 'Request Failed',
                    'data': {}
                }
            else:
                if 'status' not in req:
                    return {
                        'status': False,
                        'message': 'Request Failed',
                        'data': {}
                    }
                else:
                    if req['status'] == "success":
                        return {
                            'status': True,
                            'message': 'Success',
                            'data': {
                                'external_reference': req['data']['tx_ref']
                            },
                        }
                    else:
                        return {
                            'status': False,
                            'message': 'Payment Request failed',
                            'data': {},
                        }
        else:
            return {
                'status': False,
                'message': 'Provider Unavailable',
                'data': {}
            }

def process_transaction_status(db: Session, reference: str=None):
    transaction = get_transaction_by_reference(db=db, reference=reference)
    if transaction is None:
        return {
            'status': False,
            'message': 'Transaction not found',
            'data': None
        }
    else:
        external_reference = transaction.external_reference
        service = get_service_by_id(db=db, id=transaction.service_id)
        if service is None:
            return {
                'status': False,
                'message': 'Service not found',
                'data': None
            }
        else:
            if service.provider_id == 1:
                req = get_bill_transaction_status(reference=external_reference)
                if req is None:
                    return {
                        'status': False,
                        'message': 'Request failed',
                        'data': None
                    }
                else:
                    if 'status' not in req:
                        return {
                            'status': False,
                            'message': 'Request failed',
                            'data': None
                        }
                    else:
                        if req['status'] != 'success':
                            return {
                                'status': False,
                                'message': 'Transaction Request Failed',
                                'data': None,
                            }
                        else:
                            token = req['data']['token']
                            update_transaction(db=db, id=transaction.id, values={'status': 1})
                            return {
                                'status': True,
                                'message': 'Success',
                                'data': token,
                            }
            else:
                return {
                    'status': False,
                    'message': 'Provider unavailable',
                    'data': None
                }

def generate_service_fee(amount: float=0, fee: float=0, commission: float=0, commision_on_fee: int=0) -> float:
    total_amount = 0
    if commision_on_fee == 0:
        total_amount = float(amount * commission)
    else:
        total_amount = float(fee * commission)
    return float(total_amount)

def pay_bill(db: Session, service_code: str=None, customer_id: int=0, nuban: str=None, amount: float=0, channel_id: int=0, biller_customer: str=None, ip_address: str=None):
    service = get_service_by_code(db=db, code=service_code)
    if service is None:
        return {
            'status': False,
            'message': 'Service not found',
            'data': {},
        }
    else:
        ref = generate_external_ref()
        credit_account = get_TSS_bill()
        if credit_account == {}:
            return {
                'status': False,
                'message': 'TSS not found',
                'data': {},
            }
        else:
            credit_account_fee = get_TSS_bill_fee()
            if credit_account_fee == {}:
                return {
                    'status': False,
                    'message': 'Fee TSS not found',
                    'data': {},
                }
            else:
                customer = get_customer_info_by_id(id=customer_id)
                if customer == {}:
                    return {
                        'status': False,
                        'message': 'Customer not found',
                        'data': {},
                    }
                else:
                    account = get_account_by_account_number(account_number=nuban)
                    if account == {}:
                        return {
                            'status': False,
                            'message': 'Account not found',
                            'data': {},
                        }
                    else:
                        total_fee = generate_service_fee(amount=amount, fee=service.fee, commission=service.commission, commision_on_fee=service.commision_on_fee)
                        total_amount = amount + total_fee
                        available_balance = account['available_balance']
                        if available_balance < total_amount:
                            return {
                                'status': False,
                                'message': 'Account balance is low',
                                'data': {},
                            }
                        else:
                            narration = "Payment for " + service.fw_biller_name
                            value_date = date.today().strftime("%d-%m-%Y")
                            ft = fund_transfer_debit_customer_account_external(nuban=nuban, channel_id=channel_id, reference=ref, narration=narration, amount=amount, commission=total_fee, value_date=value_date, ip_address=ip_address, external_biller_name=service.name, external_biller_customer_id=biller_customer, is_airtime_data=service.is_airtime)
                            if ft is None:
                                return {
                                    'status': False,
                                    'message': 'Could not debit account',
                                    'data': {},
                                }
                            else:
                                if ft['status'] == False:
                                    return {
                                        'status': False,
                                        'message': ft['message'],
                                        'data': {},
                                    }
                                else:
                                    trans_id = ft['data']
                                    transaction = create_transaction(db=db, country_id=1, provider_id=service.provider_id, service_id=service.id, reference=ref, transaction_type=2, amount=amount, fee=total_fee)
                                    pay_bill = process_service_payment(db=db, service_id=service.id, amount=amount, reference=ref, biller_name=service.fw_biller_name, customer=biller_customer)
                                    if pay_bill['status'] == False:
                                        update_transaction(db=db, id=transaction.id, values={'status': 2})
                                        cancel_transaction(id=trans_id)
                                        return {
                                            'status': False,
                                            'message': pay_bill['message'],
                                            'data': {},
                                        }
                                    else:
                                        external_reference = pay_bill['data']['external_reference']
                                        update_transaction(db=db, id=transaction.id, values={'external_reference': external_reference})
                                        token = None
                                        prod = process_transaction_status(db=db, reference=external_reference)
                                        if prod['status'] == True:
                                            token = prod['data']
                                            update_transaction(db=db, id=transaction.id, values={'status': 1})
                                        approve_transaction(id=trans_id, external_biller_token=token)
                                        return {
                                            'status': True,
                                            'message': 'Success',
                                            'data': {
                                                'reference': ref
                                            }
                                        }
                                
                                