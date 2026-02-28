import pytest

from inf349 import create_app, db, Order, Product


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test_ui_payment.db"
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
            id=777,
            name="Produit UI",
            description="Produit test interface",
            price=12.0,
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


def payment_form_data():
    return {
        "credit_card_name": "Client UI",
        "credit_card_number": "4242 4242 4242 4242",
        "credit_card_expiration_year": "2030",
        "credit_card_expiration_month": "12",
        "credit_card_cvv": "123",
    }


def test_ui_shows_card_declined_message(client, monkeypatch):
    product = seed_product()
    order_id = create_order_with_api(client, product.id)

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

    response = client.post(f"/ui/order/{order_id}", data=payment_form_data())

    assert response.status_code == 200
    assert "Paiement refusé : la carte de crédit a été refusée." in response.get_data(as_text=True)


def test_ui_shows_already_paid_message(client):
    product = seed_product()
    order_id = create_order_with_api(client, product.id)

    db.connect(reuse_if_open=True)
    try:
        order = Order.get_by_id(order_id)
        order.paid = True
        order.save()
    finally:
        db.close()

    response = client.post(f"/ui/order/{order_id}", data=payment_form_data())

    assert response.status_code == 200
    assert "Cette commande est déjà payée." in response.get_data(as_text=True)
