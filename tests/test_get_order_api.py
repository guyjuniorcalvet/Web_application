"""
Tests d'API pour la consultation d'une commande (GET /order/<id>)
"""
import os
import tempfile
import pytest

from inf349 import create_app, db, Product, Order


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    db.init(path)

    db.connect()
    db.create_tables([Product, Order])
    Product.create(
        id=1,
        name="Produit en stock",
        description="desc",
        price=10.0,
        in_stock=True,
        weight=400,
        image="1.jpg",
    )

    Order.create(
        id=1,
        product_id=1,
        quantity=2,
        total_price=20.0,
        total_price_tax=20.0,
        shipping_price=None,
        paid=False,
    )

    Order.create(
        id=2,
        product_id=1,
        quantity=1,
        total_price=10.0,
        total_price_tax=11.5,
        shipping_price=5.0,
        email="john@example.com",
        shipping_country="Canada",
        shipping_address="1 rue du Test",
        shipping_postal_code="G7X 3Y7",
        shipping_city="Chicoutimi",
        shipping_province="QC",
        paid=True,
        credit_card_name="John Doe",
        credit_card_first_digits="4242",
        credit_card_last_digits="4242",
        credit_card_expiration_year=2027,
        credit_card_expiration_month=9,
        transaction_id="txn_test_1",
        transaction_success=True,
        transaction_amount_charged=1650.0,
    )
    db.close()

    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client

    if not db.is_closed():
        db.close()
    if os.path.exists(path):
        os.remove(path)


def test_get_order_existing_returns_complete_json_structure(client):
    response = client.get("/order/1")
    assert response.status_code == 200

    payload = response.get_json()
    assert "order" in payload
    order = payload["order"]

    assert order["id"] == 1
    assert order["product"] == {"id": 1, "quantity": 2}
    assert order["total_price"] == 20.0
    assert order["paid"] is False
    assert order["email"] is None
    assert order["shipping_information"] == {}
    assert order["credit_card"] == {}
    assert order["transaction"] == {}


def test_get_order_not_found_returns_404(client):
    response = client.get("/order/9999")
    assert response.status_code == 404
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "not-found",
                "name": "La commande demandée est introuvable",
            }
        }
    }


def test_get_paid_order_returns_credit_card_and_transaction(client):
    response = client.get("/order/2")
    assert response.status_code == 200

    order = response.get_json()["order"]
    assert order["paid"] is True
    assert order["email"] == "john@example.com"
    assert order["shipping_information"] == {
        "country": "Canada",
        "address": "1 rue du Test",
        "postal_code": "G7X 3Y7",
        "city": "Chicoutimi",
        "province": "QC",
    }
    assert order["credit_card"] == {
        "name": "John Doe",
        "first_digits": "4242",
        "last_digits": "4242",
        "expiration_year": 2027,
        "expiration_month": 9,
    }
    assert order["transaction"] == {
        "id": "txn_test_1",
        "success": True,
        "amount_charged": 1650.0,
    }
