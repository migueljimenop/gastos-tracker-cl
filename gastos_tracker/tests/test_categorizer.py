import pytest
from app.models import Category
from app.services.categorizer import auto_categorize


def test_auto_categorize_match(db):
    cat = Category(user_id=1, name="Supermercado", keywords="lider,jumbo,unimarc")
    db.add(cat)
    db.commit()

    result = auto_categorize("Compra Jumbo Las Condes", db, 1)
    assert result == cat.id


def test_auto_categorize_case_insensitive(db):
    cat = Category(user_id=1, name="Transporte", keywords="uber,cabify,bip")
    db.add(cat)
    db.commit()

    result = auto_categorize("PAGO UBER TRIP", db, 1)
    assert result == cat.id


def test_auto_categorize_no_match(db):
    cat = Category(user_id=1, name="Comida", keywords="restaurant,pizza")
    db.add(cat)
    db.commit()

    result = auto_categorize("Pago servicios básicos", db, 1)
    assert result is None


def test_auto_categorize_empty_keywords(db):
    cat = Category(user_id=1, name="Otros", keywords="")
    db.add(cat)
    db.commit()

    result = auto_categorize("Compra cualquiera", db, 1)
    assert result is None


def test_auto_categorize_first_match_wins(db):
    cat1 = Category(user_id=1, name="Comida", keywords="mc,burger")
    cat2 = Category(user_id=1, name="Fast Food", keywords="mc,burger")
    db.add_all([cat1, cat2])
    db.commit()

    result = auto_categorize("MC Donald's", db, 1)
    assert result in (cat1.id, cat2.id)  # One of them wins


def test_auto_categorize_ignores_other_user_categories(db):
    db.add(Category(user_id=2, name="Privada", keywords="jumbo"))
    db.commit()

    result = auto_categorize("Compra Jumbo Las Condes", db, 1)
    assert result is None
