from sqlalchemy.orm import Session
from app.models import Category


def auto_categorize(description: str, db: Session) -> int | None:
    """
    Match a transaction description to a category using keyword matching.
    Returns the category_id of the best match, or None if no match found.
    """
    description_lower = description.lower()
    categories = db.query(Category).all()

    for category in categories:
        for keyword in category.keyword_list():
            if keyword in description_lower:
                return category.id

    return None
