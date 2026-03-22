from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from app.models import Category


def auto_categorize(description: str, db: Session, user_id: int) -> Optional[int]:
    """
    Match a transaction description to a category using keyword matching.
    Returns the category_id of the best match, or None if no match found.
    """
    description_lower = description.lower()
    categories = db.query(Category).filter(Category.user_id == user_id).all()

    for category in categories:
        for keyword in category.keyword_list():
            if keyword in description_lower:
                return category.id

    return None
