"""
Tests d'API pour la mise a jour client d'une commande (PUT /order/<id>)
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
    db.close()

    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client

    if not db.is_closed():
        db.close()
    if os.path.exists(path):
        os.remove(path)


def test_put_order_client_success_updates_customer_fields(client):
    payload = {
        "order": {
            "email": "john@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "201, rue President-Kennedy",
                "postal_code": "G7X 3Y7",
                "city": "Chicoutimi",
                "province": "QC",
            },
        }
    }
    response = client.put("/order/1", json=payload)
    assert response.status_code == 200

    order = response.get_json()["order"]
    assert order["id"] == 1
    assert order["email"] == "john@example.com"
    assert order["shipping_information"] == {
        "country": "Canada",
        "address": "201, rue President-Kennedy",
        "postal_code": "G7X 3Y7",
        "city": "Chicoutimi",
        "province": "QC",
    }
    assert order["product"] == {"id": 1, "quantity": 2}


def test_put_order_client_not_found_returns_404(client):
    response = client.put(
        "/order/9999",
        json={
            "order": {
                "email": "john@example.com",
                "shipping_information": {
                    "country": "Canada",
                    "address": "A",
                    "postal_code": "B",
                    "city": "C",
                    "province": "QC",
                },
            }
        },
    )
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["errors"]["order"]["code"] == "not-found"
    assert "introuvable" in payload["errors"]["order"]["name"].lower()


def test_put_order_client_missing_fields_returns_422(client):
    response = client.put(
        "/order/1",
        json={
            "order": {
                "shipping_information": {
                    "country": "Canada",
                    "address": "A",
                    "postal_code": "B",
                    "city": "C",
                    "province": "QC",
                }
            }
        },
    )
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "missing-fields",
                "name": "Il manque un ou plusieurs champs qui sont obligatoires",
            }
        }
    }


def test_put_order_client_rejects_forbidden_order_fields(client):
    response = client.put(
        "/order/1",
        json={
            "order": {
                "email": "john@example.com",
                "shipping_information": {
                    "country": "Canada",
                    "address": "A",
                    "postal_code": "B",
                    "city": "C",
                    "province": "QC",
                },
                "total_price": 9999,
            }
        },
    )
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "missing-fields",
                "name": "Il manque un ou plusieurs champs qui sont obligatoires",
            }
        }
    }


def test_put_order_client_rejects_mixed_order_and_credit_card_payload(client):
    response = client.put(
        "/order/1",
        json={
            "order": {
                "email": "john@example.com",
                "shipping_information": {
                    "country": "Canada",
                    "address": "A",
                    "postal_code": "B",
                    "city": "C",
                    "province": "QC",
                },
            },
            "credit_card": {},
        },
    )
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "missing-fields",
                "name": "Il manque un ou plusieurs champs qui sont obligatoires",
            }
        }
    }
