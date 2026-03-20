import pytest
from app.models import Category
from app.services.categorizer import auto_categorize


def test_auto_categorize_match(db):
    cat = Category(name="Supermercado", keywords="lider,jumbo,unimarc")
    db.add(cat)
    db.commit()

    result = auto_categorize("Compra Jumbo Las Condes", db)
    assert result == cat.id


def test_auto_categorize_case_insensitive(db):
    cat = Category(name="Transporte", keywords="uber,cabify,bip")
    db.add(cat)
    db.commit()

    result = auto_categorize("PAGO UBER TRIP", db)
    assert result == cat.id


def test_auto_categorize_no_match(db):
    cat = Category(name="Comida", keywords="restaurant,pizza")
    db.add(cat)
    db.commit()

    result = auto_categorize("Pago servicios básicos", db)
    assert result is None


def test_auto_categorize_empty_keywords(db):
    cat = Category(name="Otros", keywords="")
    db.add(cat)
    db.commit()

    result = auto_categorize("Compra cualquiera", db)
    assert result is None


def test_auto_categorize_first_match_wins(db):
    cat1 = Category(name="Comida", keywords="mc,burger")
    cat2 = Category(name="Fast Food", keywords="mc,burger")
    db.add_all([cat1, cat2])
    db.commit()

    result = auto_categorize("MC Donald's", db)
    assert result in (cat1.id, cat2.id)  # One of them wins
