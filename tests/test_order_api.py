"""
Tests d'API pour la creation de commande (POST /order)
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
    Product.create(
        id=2,
        name="Produit hors stock",
        description="desc",
        price=20.0,
        in_stock=False,
        weight=600,
        image="2.jpg",
    )
    db.close()

    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client

    if not db.is_closed():
        db.close()
    if os.path.exists(path):
        os.remove(path)


def test_create_order_success_returns_302_and_location(client):
    response = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    assert response.status_code == 302
    assert response.headers.get("Location", "").startswith("/order/")


def test_create_order_sets_shipping_price_based_on_weight(client):
    response = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    assert response.status_code == 302

    location = response.headers.get("Location", "")
    order_id = int(location.rsplit("/", 1)[-1])
    order = Order.get_by_id(order_id)

    assert order.total_price == 20.0
    assert order.shipping_price == 10.0
    assert order.total_price_tax == 20.0


def test_create_order_missing_product_returns_missing_fields(client):
    response = client.post("/order", json={})
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "product": {
                "code": "missing-fields",
                "name": "La création d'une commande nécessite un produit",
            }
        }
    }


def test_create_order_quantity_less_than_one_returns_missing_fields(client):
    response = client.post("/order", json={"product": {"id": 1, "quantity": 0}})
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "product": {
                "code": "missing-fields",
                "name": "La création d'une commande nécessite un produit",
            }
        }
    }


def test_create_order_unknown_product_returns_out_of_inventory(client):
    response = client.post("/order", json={"product": {"id": 9999, "quantity": 1}})
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "product": {
                "code": "out-of-inventory",
                "name": "Le produit demandé n'est pas en inventaire",
            }
        }
    }


def test_create_order_out_of_stock_product_returns_out_of_inventory(client):
    response = client.post("/order", json={"product": {"id": 2, "quantity": 1}})
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "product": {
                "code": "out-of-inventory",
                "name": "Le produit demandé n'est pas en inventaire",
            }
        }
    }
