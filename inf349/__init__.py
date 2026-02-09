from flask import Flask, jsonify
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

