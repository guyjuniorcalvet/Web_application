"""
Tests d'API pour le paiement d'une commande (PUT /order/<id> avec credit_card)
"""
import os
import tempfile
import pytest

from inf349 import create_app, db, Product, Order


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


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

    # Commande prete pour paiement
    Order.create(
        id=1,
        product_id=1,
        quantity=2,
        total_price=20.0,
        shipping_price=5.0,
        total_price_tax=23.0,
        email="john@example.com",
        shipping_country="Canada",
        shipping_address="1 rue du Test",
        shipping_postal_code="G7X 3Y7",
        shipping_city="Chicoutimi",
        shipping_province="QC",
        paid=False,
    )

    # Commande deja payee
    Order.create(
        id=2,
        product_id=1,
        quantity=1,
        total_price=10.0,
        shipping_price=5.0,
        total_price_tax=11.5,
        email="already@paid.com",
        shipping_country="Canada",
        shipping_address="2 rue du Test",
        shipping_postal_code="G7X 3Y7",
        shipping_city="Chicoutimi",
        shipping_province="QC",
        paid=True,
        credit_card_name="John Doe",
        credit_card_first_digits="4242",
        credit_card_last_digits="4242",
        credit_card_expiration_year=2027,
        credit_card_expiration_month=9,
        transaction_id="txn_already_paid",
        transaction_success=True,
        transaction_amount_charged=1150.0,
    )

    # Commande sans infos client
    Order.create(
        id=3,
        product_id=1,
        quantity=1,
        total_price=10.0,
        shipping_price=None,
        total_price_tax=10.0,
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


def valid_credit_card_payload():
    return {
        "credit_card": {
            "name": "John Doe",
            "number": "4242 4242 4242 4242",
            "expiration_year": 2027,
            "expiration_month": 9,
            "cvv": "123",
        }
    }


def test_put_order_payment_rejects_when_customer_info_is_missing(client):
    response = client.put("/order/3", json=valid_credit_card_payload())
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "missing-fields",
                "name": "Les informations du client sont nécessaire avant d'appliquer une carte de crédit",
            }
        }
    }


def test_put_order_payment_rejects_when_order_is_already_paid(client):
    response = client.put("/order/2", json=valid_credit_card_payload())
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "already-paid",
                "name": "La commande a déjà été payée.",
            }
        }
    }


def test_put_order_payment_success_persists_card_and_transaction(client, monkeypatch):
    captured_payload = {}

    def fake_post(*args, **kwargs):
        captured_payload["json"] = args[1] if len(args) > 1 else {}
        return FakeResponse(
            200,
            {
                "credit_card": {
                    "name": "John Doe",
                    "first_digits": "4242",
                    "last_digits": "4242",
                    "expiration_year": 2027,
                    "expiration_month": 9,
                },
                "transaction": {
                    "id": "txn_success_1",
                    "success": True,
                    "amount_charged": 2500,
                },
            },
        )

    monkeypatch.setattr("inf349.http_post_json", fake_post)

    response = client.put("/order/1", json=valid_credit_card_payload())
    assert response.status_code == 200

    order = response.get_json()["order"]
    assert order["paid"] is True
    assert order["credit_card"] == {
        "name": "John Doe",
        "first_digits": "4242",
        "last_digits": "4242",
        "expiration_year": 2027,
        "expiration_month": 9,
    }
    assert order["transaction"] == {
        "id": "txn_success_1",
        "success": True,
        "amount_charged": 2500,
    }
    assert captured_payload["json"]["amount_charged"] == 2500


def test_put_order_payment_propagates_remote_422_error(client, monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(
            422,
            {
                "errors": {
                    "credit_card": {
                        "code": "card-declined",
                        "name": "La carte de crédit a été déclinée.",
                    }
                }
            },
        )

    monkeypatch.setattr("inf349.http_post_json", fake_post)

    response = client.put("/order/1", json=valid_credit_card_payload())
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "credit_card": {
                "code": "card-declined",
                "name": "La carte de crédit a été déclinée.",
            }
        }
    }


def test_put_order_payment_rejects_when_credit_card_fields_are_missing(client):
    response = client.put(
        "/order/1",
        json={
            "credit_card": {
                "name": "John Doe",
                "number": "4242 4242 4242 4242",
            }
        },
    )
    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "credit_card": {
                "code": "missing-fields",
                "name": "Certains champs de la carte sont manquants",
            }
        }
    }
