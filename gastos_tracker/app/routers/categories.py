from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Category, User
from app.schemas import CategoryCreate, CategoryUpdate, CategoryOut
from app.services.audit import record_audit_event

router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Category).filter(Category.user_id == current_user.id).all()


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Category).filter(Category.user_id == current_user.id, Category.name == data.name).first():
        raise HTTPException(status_code=409, detail="Category name already exists")
    category = Category(**data.model_dump(), user_id=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    record_audit_event(
        db,
        action="category.created",
        entity_type="category",
        entity_id=category.id,
        user_id=current_user.id,
        details={"name": category.name},
    )
    db.commit()
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if data.name and data.name != category.name:
        duplicate = (
            db.query(Category)
            .filter(
                Category.user_id == current_user.id,
                Category.name == data.name,
                Category.id != category.id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Category name already exists")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    record_audit_event(
        db,
        action="category.updated",
        entity_type="category",
        entity_id=category.id,
        user_id=current_user.id,
        details={"changed_fields": sorted(data.model_dump(exclude_none=True).keys())},
    )
    db.commit()
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    record_audit_event(
        db,
        action="category.deleted",
        entity_type="category",
        entity_id=category.id,
        user_id=current_user.id,
        details={"name": category.name},
    )
    db.delete(category)
    db.commit()
