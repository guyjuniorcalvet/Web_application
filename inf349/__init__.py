from flask import Flask, jsonify, render_template, request, redirect, url_for
import os
import requests
import click
from peewee import *

# Database setup
db = SqliteDatabase('database.db')

class BaseModel(Model):
    class Meta:
        database = db

class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    price = FloatField()
    in_stock = BooleanField()
    weight = IntegerField()
    image = CharField()

class Order(BaseModel):
    id = AutoField()
    # Product details
    product_id = IntegerField()
    quantity = IntegerField()
    # Calculated fields
    total_price = FloatField(null=True)
    shipping_price = FloatField(null=True)
    total_price_tax = FloatField(null=True)
    # Customer details
    email = CharField(null=True)
    shipping_country = CharField(null=True)
    shipping_address = CharField(null=True)
    shipping_postal_code = CharField(null=True)
    shipping_city = CharField(null=True)
    shipping_province = CharField(null=True)
    # Payment details
    paid = BooleanField(default=False)
    credit_card_name = CharField(null=True)
    credit_card_first_digits = CharField(null=True)
    credit_card_last_digits = CharField(null=True)
    credit_card_expiration_year = IntegerField(null=True)
    credit_card_expiration_month = IntegerField(null=True)
    transaction_id = CharField(null=True)
    transaction_success = BooleanField(null=True)
    transaction_amount_charged = FloatField(null=True)


def serialize_order(order):
    shipping_information = {}
    if (
        order.shipping_country is not None
        or order.shipping_address is not None
        or order.shipping_postal_code is not None
        or order.shipping_city is not None
        or order.shipping_province is not None
    ):
        shipping_information = {
            "country": order.shipping_country,
            "address": order.shipping_address,
            "postal_code": order.shipping_postal_code,
            "city": order.shipping_city,
            "province": order.shipping_province,
        }

    credit_card = {}
    if (
        order.credit_card_name is not None
        or order.credit_card_first_digits is not None
        or order.credit_card_last_digits is not None
        or order.credit_card_expiration_year is not None
        or order.credit_card_expiration_month is not None
    ):
        credit_card = {
            "name": order.credit_card_name,
            "first_digits": order.credit_card_first_digits,
            "last_digits": order.credit_card_last_digits,
            "expiration_year": order.credit_card_expiration_year,
            "expiration_month": order.credit_card_expiration_month,
        }

    transaction = {}
    if (
        order.transaction_id is not None
        or order.transaction_success is not None
        or order.transaction_amount_charged is not None
    ):
        transaction = {
            "id": order.transaction_id,
            "success": order.transaction_success,
            "amount_charged": order.transaction_amount_charged,
        }

    return {
        "id": order.id,
        "total_price": order.total_price,
        "total_price_tax": order.total_price_tax,
        "email": order.email,
        "credit_card": credit_card,
        "shipping_information": shipping_information,
        "paid": order.paid,
        "transaction": transaction,
        "product": {
            "id": order.product_id,
            "quantity": order.quantity,
        },
        "shipping_price": order.shipping_price,
    }


def missing_order_fields_response():
    return jsonify({
        "errors": {
            "order": {
                "code": "missing-fields",
                "name": "Il manque un ou plusieurs champs qui sont obligatoires"
            }
        }
    }), 422


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'inf349.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.before_request
    def before_request():
        db.connect()

    @app.after_request
    def after_request(response):
        db.close()
        return response

    @app.route('/')
    def list_products():
        products = list(Product.select().dicts())
        return jsonify({'products': products})

    @app.route('/order', methods=['POST'])
    def create_order():
        payload = request.get_json(silent=True) or {}
        product_payload = payload.get('product')

        if (
            not isinstance(product_payload, dict)
            or 'id' not in product_payload
            or 'quantity' not in product_payload
        ):
            return jsonify({
                "errors": {
                    "product": {
                        "code": "missing-fields",
                        "name": "La création d'une commande nécessite un produit"
                    }
                }
            }), 422

        try:
            product_id = int(product_payload['id'])
            quantity = int(product_payload['quantity'])
        except (TypeError, ValueError):
            return jsonify({
                "errors": {
                    "product": {
                        "code": "missing-fields",
                        "name": "La création d'une commande nécessite un produit"
                    }
                }
            }), 422

        if quantity < 1:
            return jsonify({
                "errors": {
                    "product": {
                        "code": "missing-fields",
                        "name": "La création d'une commande nécessite un produit"
                    }
                }
            }), 422

        product = Product.get_or_none(Product.id == product_id)
        if not product or not product.in_stock:
            return jsonify({
                "errors": {
                    "product": {
                        "code": "out-of-inventory",
                        "name": "Le produit demandé n'est pas en inventaire"
                    }
                }
            }), 422

        total_price = product.price * quantity
        order = Order.create(
            product_id=product.id,
            quantity=quantity,
            total_price=total_price,
            total_price_tax=total_price
        )

        response = jsonify({})
        response.status_code = 302
        response.headers['Location'] = f"/order/{order.id}"
        return response

    @app.route('/order/<int:order_id>', methods=['GET'])
    def get_order(order_id):
        order = Order.get_or_none(Order.id == order_id)
        if order is None:
            return jsonify({
                "errors": {
                    "order": {
                        "code": "not-found",
                        "name": "La commande demandée est introuvable"
                    }
                }
            }), 404

        return jsonify({"order": serialize_order(order)}), 200

    @app.route('/order/<int:order_id>', methods=['PUT'])
    def update_order_client(order_id):
        order = Order.get_or_none(Order.id == order_id)
        if order is None:
            return jsonify({
                "errors": {
                    "order": {
                        "code": "not-found",
                        "name": "La commande demandée est introuvable"
                    }
                }
            }), 404

        payload = request.get_json(silent=True) or {}
        if set(payload.keys()) != {"order"}:
            return missing_order_fields_response()

        order_payload = payload.get('order')
        if not isinstance(order_payload, dict):
            return missing_order_fields_response()

        allowed_order_fields = {"email", "shipping_information"}
        if set(order_payload.keys()) - allowed_order_fields:
            return missing_order_fields_response()

        email = order_payload.get('email')
        shipping_information = order_payload.get('shipping_information')

        if not isinstance(email, str) or not email.strip():
            return missing_order_fields_response()

        if not isinstance(shipping_information, dict):
            return missing_order_fields_response()

        required_shipping_fields = {
            "country",
            "address",
            "postal_code",
            "city",
            "province",
        }
        if required_shipping_fields - set(shipping_information.keys()):
            return missing_order_fields_response()

        for field in required_shipping_fields:
            value = shipping_information.get(field)
            if not isinstance(value, str) or not value.strip():
                return missing_order_fields_response()

        order.email = email.strip()
        order.shipping_country = shipping_information["country"].strip()
        order.shipping_address = shipping_information["address"].strip()
        order.shipping_postal_code = shipping_information["postal_code"].strip()
        order.shipping_city = shipping_information["city"].strip()
        order.shipping_province = shipping_information["province"].strip()
        order.save()

        return jsonify({"order": serialize_order(order)}), 200

    @app.route('/ui/order', methods=['GET', 'POST'])
    def ui_order_form():
        products = list(Product.select().order_by(Product.name))

        if request.method == 'POST':
            product_id = request.form.get('product_id', '').strip()
            quantity = request.form.get('quantity', '').strip()

            try:
                product_id = int(product_id)
                quantity = int(quantity)
            except ValueError:
                return render_template(
                    'order_form.html',
                    products=products,
                    error="Veuillez fournir un produit et une quantité valides."
                ), 422

            if quantity < 1:
                return render_template(
                    'order_form.html',
                    products=products,
                    error="La quantité doit être supérieure ou égale à 1."
                ), 422

            try:
                product = Product.get_by_id(product_id)
            except Product.DoesNotExist:
                return render_template(
                    'order_form.html',
                    products=products,
                    error="Le produit sélectionné est introuvable."
                ), 404

            if not product.in_stock:
                return render_template(
                    'order_form.html',
                    products=products,
                    error="Le produit sélectionné n'est pas en inventaire."
                ), 422

            total_price = product.price * quantity

            order = Order.create(
                product_id=product.id,
                quantity=quantity,
                total_price=total_price,
                total_price_tax=total_price
            )

            return redirect(url_for('ui_order_confirmation', order_id=order.id))

        return render_template('order_form.html', products=products)

    @app.route('/ui/order/<int:order_id>')
    def ui_order_confirmation(order_id):
        try:
            order = Order.get_by_id(order_id)
            product = Product.get_by_id(order.product_id)
        except (Order.DoesNotExist, Product.DoesNotExist):
            return "Commande introuvable.", 404

        return render_template(
            'order_confirmation.html',
            order=order,
            product=product
        )

    # Register the init-db command
    app.cli.add_command(init_db_command)

    return app

def init_db():
    """Clear existing data and create new tables."""
    db.connect()
    db.drop_tables([Product, Order], safe=True)
    db.create_tables([Product, Order])
    
    # Fetch products from remote service and populate the database
    try:
        products_url = 'http://dimensweb.uqac.ca/~jgnault/shops/products/'
        response = requests.get(products_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        products_data = response.json().get('products', [])
        
        with db.atomic():
            for product_data in products_data:
                Product.create(**product_data)
        print(f"Successfully fetched and stored {len(products_data)} products.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching products: {e}")
    
    db.close()


@click.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')
