import logging
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

from database import SessionLocal, Account, Transaction

# --- App Configuration ---
API_KEY_CREDENTIAL = "super-secret-key"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom observability metrics
FRAUD_COUNTER = Counter("fraud_alerts_total", "Total count of transactions flagged as fraud")

app = FastAPI(title="Risk Alert API")
Instrumentator().instrument(app).expose(app)

# --- Schemas ---
class TransactionRequest(BaseModel):
    account_id: int
    amount: float

# --- Dependencies ---
def get_db():
    """Yields a database session and ensures it closes after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(x_api_key: str = Header(...)):
    """Validates the API key provided in the request headers."""
    if x_api_key != API_KEY_CREDENTIAL:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# --- Event Handlers ---
@app.on_event("startup")
def seed_db():
    """Ensures a test account exists in the database on startup."""
    db = SessionLocal()
    if not db.query(Account).filter(Account.id == 1).first():
        logger.info("Seeding database with initial test account.")
        test_account = Account(id=1, customer_name="Test User", balance=100000.0, status="active")
        db.add(test_account)
        db.commit()
    db.close()

# --- API Endpoints ---
@app.post("/transactions/", dependencies=[Depends(verify_api_key)])
def create_transaction(request: TransactionRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == request.account_id).first()
    
    if not account:
        logger.error(f"Transaction failed: Account {request.account_id} not found")
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Business Logic 1: Validate sufficient funds
    if account.balance < request.amount:
        status = "declined"
        logger.info(f"Transaction declined: Insufficient funds for Account {request.account_id}")
        new_tx = Transaction(account_id=request.account_id, amount=request.amount, status=status)
        db.add(new_tx)
        db.commit()
        return {"status": status, "reason": "Insufficient funds"}
    
    # Business Logic 2: Risk and fraud controls
    if request.amount > 10000:
        status = "flagged_for_fraud"
        FRAUD_COUNTER.inc()
        logger.warning(f"FRAUD ALERT: Transaction of £{request.amount} for Account {request.account_id}")
    else:
        status = "approved"
        account.balance -= request.amount

    # Persist transaction record
    new_tx = Transaction(account_id=request.account_id, amount=request.amount, status=status)
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    
    return {"transaction_id": new_tx.id, "status": status, "new_balance": account.balance}

@app.get("/accounts/{id}/statement", dependencies=[Depends(verify_api_key)])
def get_statement(id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Retrieve the 5 most recent transactions
    transactions = db.query(Transaction).filter(Transaction.account_id == id)\
        .order_by(Transaction.timestamp.desc()).limit(5).all()
    
    return {
        "customer_name": account.customer_name,
        "current_balance": account.balance,
        "recent_transactions": [
            {
                "id": t.id, 
                "amount": t.amount, 
                "status": t.status, 
                "timestamp": t.timestamp.isoformat()
            } for t in transactions
        ]
    }