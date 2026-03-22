from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Budget, Category, User
from app.schemas import BudgetCreate, BudgetUpdate, BudgetOut
from app.services.audit import record_audit_event
from app.services.alerts import get_budget_alerts

router = APIRouter(prefix="/budgets", tags=["budgets"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Budget).filter(Budget.user_id == current_user.id).all()


@router.post("/", response_model=BudgetOut, status_code=201)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = (
        db.query(Category)
        .filter(Category.id == data.category_id, Category.user_id == current_user.id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    existing = (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id, Budget.category_id == data.category_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="A budget for this category already exists")
    budget = Budget(**data.model_dump(), user_id=current_user.id)
    db.add(budget)
    db.commit()
    db.refresh(budget)
    record_audit_event(
        db,
        action="budget.created",
        entity_type="budget",
        entity_id=budget.id,
        user_id=current_user.id,
        details={"category_id": budget.category_id, "monthly_limit": budget.monthly_limit},
    )
    db.commit()
    return budget


@router.patch("/{budget_id}", response_model=BudgetOut)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    record_audit_event(
        db,
        action="budget.updated",
        entity_type="budget",
        entity_id=budget.id,
        user_id=current_user.id,
        details={"changed_fields": sorted(data.model_dump(exclude_none=True).keys())},
    )
    db.commit()
    return budget


@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    record_audit_event(
        db,
        action="budget.deleted",
        entity_type="budget",
        entity_id=budget.id,
        user_id=current_user.id,
        details={"category_id": budget.category_id},
    )
    db.delete(budget)
    db.commit()


@router.get("/alerts/current")
def current_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns budgets that have reached or exceeded their alert threshold this month."""
    return get_budget_alerts(db, current_user.id)
