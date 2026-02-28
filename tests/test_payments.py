import pytest

from inf349 import create_app, db, Order, Product


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test_payments.db"
    db.init(str(db_path))
    db.connect(reuse_if_open=True)
    db.create_tables([Product, Order])
    db.close()

    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client

    db.connect(reuse_if_open=True)
    db.drop_tables([Order, Product], safe=True)
    db.close()


def seed_product():
    db.connect(reuse_if_open=True)
    try:
        return Product.create(
            id=999,
            name="Produit test",
            description="Produit pour test paiement",
            price=10.0,
            in_stock=True,
            weight=200,
            image="img.jpg",
        )
    finally:
        db.close()


def create_order_with_api(client, product_id):
    response = client.post(
        "/order",
        json={"product": {"id": product_id, "quantity": 1}},
    )
    assert response.status_code == 302
    location = response.headers["Location"]
    return int(location.rsplit("/", 1)[-1])


def build_payload():
    return {
        "credit_card": {
            "name": "Jean Client",
            "number": "4242 4242 4242 4242",
            "expiration_year": 2030,
            "expiration_month": 12,
            "cvv": "123",
        }
    }


def set_customer_info_with_api(client, order_id):
    response = client.put(
        f"/order/{order_id}",
        json={
            "order": {
                "email": "client@example.com",
                "shipping_information": {
                    "country": "CA",
                    "address": "123 Rue Test",
                    "postal_code": "G1G1G1",
                    "city": "Québec",
                    "province": "QC",
                },
            }
        },
    )
    assert response.status_code == 200


def test_card_declined_is_normalized(client, monkeypatch):
    product = seed_product()
    order_id = create_order_with_api(client, product.id)
    set_customer_info_with_api(client, order_id)

    class FakeResponse:
        status_code = 422
        text = "card declined"

        @staticmethod
        def json():
            return {
                "errors": {
                    "credit_card": {
                        "code": "card_declined",
                        "name": "Carte refusée",
                    }
                }
            }

    monkeypatch.setattr("inf349.http_post_json", lambda *args, **kwargs: FakeResponse())

    response = client.put(f"/order/{order_id}", json=build_payload())

    assert response.status_code == 422
    body = response.get_json()
    assert body["errors"]["credit_card"]["code"] == "card-declined"


def test_double_payment_is_blocked(client, monkeypatch):
    product = seed_product()
    order_id = create_order_with_api(client, product.id)
    set_customer_info_with_api(client, order_id)

    calls = {"count": 0}

    class FakeResponse:
        status_code = 200
        text = "ok"

        @staticmethod
        def json():
            return {
                "credit_card": {
                    "name": "Jean Client",
                    "first_digits": "4242",
                    "last_digits": "4242",
                    "expiration_year": 2030,
                    "expiration_month": 12,
                },
                "transaction": {
                    "id": "txn_123",
                    "success": True,
                    "amount_charged": 1150,
                },
            }

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setattr("inf349.http_post_json", fake_post)

    first_response = client.put(f"/order/{order_id}", json=build_payload())
    assert first_response.status_code == 200
    assert calls["count"] == 1

    second_response = client.put(f"/order/{order_id}", json=build_payload())
    assert second_response.status_code == 422
    second_body = second_response.get_json()
    assert second_body["errors"]["order"]["code"] == "already-paid"
    assert calls["count"] == 1
