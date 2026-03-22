from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Budget
from app.schemas import BudgetCreate, BudgetUpdate, BudgetOut
from app.services.alerts import get_budget_alerts

router = APIRouter(prefix="/budgets", tags=["budgets"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db)):
    return db.query(Budget).all()


@router.post("/", response_model=BudgetOut, status_code=201)
def create_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    existing = db.query(Budget).filter(Budget.category_id == data.category_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="A budget for this category already exists")
    budget = Budget(**data.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.patch("/{budget_id}", response_model=BudgetOut)
def update_budget(budget_id: int, data: BudgetUpdate, db: Session = Depends(get_db)):
    budget = db.get(Budget, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.get(Budget, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()


@router.get("/alerts/current")
def current_alerts(db: Session = Depends(get_db)):
    """Returns budgets that have reached or exceeded their alert threshold this month."""
    return get_budget_alerts(db)
