from flask import Flask, jsonify, render_template, request, redirect, url_for
import os
import requests
import click
from peewee import *
from inf349.taxes import calculate_total_with_tax
from inf349.shipping import calculate_shipping_price

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


def missing_customer_information_for_payment_response():
    return jsonify({
        "errors": {
            "order": {
                "code": "missing-fields",
                "name": "Les informations du client sont nécessaire avant d'appliquer une carte de crédit"
            }
        }
    }), 422


def already_paid_response():
    return jsonify({
        "errors": {
            "order": {
                "code": "already-paid",
                "name": "La commande a déjà été payée."
            }
        }
    }), 422


def has_complete_customer_information(order):
    return all([
        order.email,
        order.shipping_country,
        order.shipping_address,
        order.shipping_postal_code,
        order.shipping_city,
        order.shipping_province,
    ])


def extract_error_name(payload):
    if not isinstance(payload, dict):
        return "Une erreur est survenue pendant le paiement."

    if isinstance(payload.get("errors"), dict):
        first_error = next(iter(payload["errors"].values()), None)
        if isinstance(first_error, dict) and first_error.get("name"):
            return first_error["name"]

    if isinstance(payload.get("credit_card"), dict) and payload["credit_card"].get("name"):
        return payload["credit_card"]["name"]

    return "Une erreur est survenue pendant le paiement."


def process_payment(order, credit_card_info):
    
    #Valider que la carte de crédit est un dictionnaire
    if not isinstance(credit_card_info,dict):
        return (jsonify({
            "errors": {
                "credit_card": {
                    "code": "invalid-format",
                    "name": "Format invalide pour la carte de crédit"
                }
            }
        })), 422

    # Valider des champs requis sont présents et valides
    required_fields = {"name", "number", "expiration_year", "expiration_month", "cvv"}
    if not required_fields.issubset(credit_card_info.keys()):
        return (jsonify({
            "errors": {
                "credit_card": {
                    "code": "missing-fields",
                    "name": "Certains champs de la carte sont manquants"
                }
            }
        }), 422)
        
    # Validation du  nom du client
    name = credit_card_info.get('name')
    if not isinstance(name, str) or not name.strip():
        return (jsonify({
            "errors": {
                "credit_card": {
                    "code": "invalid-name",
                    "name": "Le nom est invalide"
                }
            }
        }), 422)
 
   # Validation du numéro de carte de crédit 
    number = credit_card_info.get('number')
    if not isinstance(number, str):
       return (jsonify({
           "errors": {
               "credit_card": {
                   "code": "incorrect-number",
                   "name": "Le numéro de carte est incorrect"
               }
           }
       }), 422)
  
    clean_number = number.replace(" ","" )

    # Validation du champ expiration_year
    try:
        expiration_year = int(credit_card_info.get('expiration_year'))
    except (TypeError, ValueError):
        return (jsonify({
            "errors": {
                "credit_card": {
                    "code": "invalid-expiration",
                    "name": "L'année d'expiration est invalide"
                }
            }
        }), 422)
        
    # Validation du champs expiration_month
    try: 
        expiration_month= int(credit_card_info.get('expiration_month'))
        if expiration_month < 1 or expiration_month > 12:
            raise ValueError("Invalid month")
    except (TypeError, ValueError):
        return (jsonify({
            "errors": {
                "credit_card": {
                    "code": "invalid-expiration",
                        "name": "Le mois d'expiration est invalide"
                    }
                }
            }), 422)

    # Validation du CVV 
    cvv=credit_card_info.get('cvv')
    if not isinstance(cvv, str) or not cvv.isdigit() or len(cvv) !=3:
        return (jsonify({
            "errors": {
                "credit_card": {
                    "code": "invalid-cvv",
                    "name": "Le CVV est incorrect"
                }
            }
        }), 422)
        
    # Convertir le prix total des taxes en cents
    amount_charged_cents = int(round(order.total_price_tax * 100))

    payment_request = {
        "credit_card": {
            "name": name.strip(),
            "number": clean_number,
            "expiration_year": expiration_year,
            "expiration_month": expiration_month,
            "cvv": cvv
        },
        "amount_charged": amount_charged_cents
    }
    
    try:
        response = requests.post(
            'http://dimprojetu.uqac.ca/~jgnault/shops/pay/',
            json=payment_request,
            timeout=10
        )
        print(f"Payment service response: {response.status_code} {response.text}") # Pour identifier le code d'erreur sur la console 
        # Si la carte de crédit est acceptée
        if response.status_code == 200:
        
            # Paiment  réussi
            payment_response = response.json()
            
            # Extraction des informations de la transaction
            transaction =  payment_response.get('transaction', {})
            response_card = payment_response.get('credit_card', {})

            
            
            order.paid = True
            order.credit_card_name = response_card.get('name')
            order.credit_card_first_digits = response_card.get('first_digits')
            order.credit_card_last_digits = response_card.get('last_digits')
            order.credit_card_expiration_year = response_card.get('expiration_year')
            order.credit_card_expiration_month = response_card.get('expiration_month')
            order.transaction_id = transaction.get('id')
            order.transaction_success = transaction.get('success')
            order.transaction_amount_charged = transaction.get('amount_charged')

            order.save()
            return None  

        elif response.status_code == 422:
            # La carte de crédit a été refusée 
            error_response = response.json()
            return (jsonify(error_response), 422)
        else:
            # Erreur  du service de paiement 
            return (jsonify({
                "errors": {
                    "payment": {
                        "code": "service-error",
                        "name": "Le service de paiement a rencontre une erreur"
                    }
                }
            }), 500)

    except requests.exceptions.RequestException:
        # Erreur de communication avec le service de paiement
        return (jsonify({
            "errors": {
                "payment": {
                    "code": "service-unavailable",
                    "name": "Le service de paiement est temporairement indisponible"
                }
            }
        }), 503)



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

    @app.errorhandler(422)
    def handle_422_error(error):
        response = getattr(error, 'description', None)
        # Si la description est déjà un dict/json, on le retourne, sinon on standardise
        if isinstance(response, dict):
            return jsonify(response), 422
        return jsonify({
            "errors": {
                "order": {
                    "code": "unprocessable-entity",
                    "name": "Erreur de validation des champs."
                }
            }
        }), 422

   

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
        return render_template('list_products.html', products=products)
    
    @app.route('/api/products')
    def api_list_products():
        """API endpoint pour obtenir les produits en JSON"""
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
        has_order_payload = "order" in payload
        has_credit_card_payload = "credit_card" in payload

        # payment and customer update must be done in separate calls
        if has_order_payload == has_credit_card_payload:
            return missing_order_fields_response()

        if has_order_payload:
            if set(payload.keys()) != {"order"}:
                return missing_order_fields_response()

            order_payload = payload.get('order')
            if not isinstance(order_payload, dict):
                return missing_order_fields_response()

            if set(order_payload.keys()) != {"email", "shipping_information"}:
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

            product = Product.get_or_none(Product.id == order.product_id)
            if product:
                total_weight = product.weight * order.quantity
                try:
                    order.shipping_price = calculate_shipping_price(total_weight)
                except ValueError:
                    order.shipping_price = 0

                province = order.shipping_province
                try:
                    subtotal = order.total_price + order.shipping_price
                    order.total_price_tax = calculate_total_with_tax(subtotal, province)
                except ValueError:
                    order.total_price_tax = order.total_price + order.shipping_price

            order.save()
            return jsonify({"order": serialize_order(order)}), 200

        # credit_card payload mode
        if set(payload.keys()) != {"credit_card"}:
            return missing_order_fields_response()

        if order.paid:
            return already_paid_response()

        if not has_complete_customer_information(order):
            return missing_customer_information_for_payment_response()

        payment_error = process_payment(order, payload.get("credit_card"))
        if payment_error is not None:
            return payment_error

        return jsonify({"order": serialize_order(order)}), 200

    @app.route('/ui/order', methods=['GET', 'POST'])
    def ui_order_form():
        products = list(Product.select().order_by(Product.name))

        if request.method == 'POST':
            product_id = request.form.get('product_id', '').strip()
            quantity = request.form.get('quantity', '').strip()
            email = request.form.get('email', '').strip()
            shipping_country = request.form.get('shipping_country', '').strip()
            shipping_address = request.form.get('shipping_address', '').strip()
            shipping_postal_code = request.form.get('shipping_postal_code', '').strip()
            shipping_city = request.form.get('shipping_city', '').strip()
            shipping_province = request.form.get('shipping_province', '').strip()

            # Validation des champs obligatoires
            if not all([product_id, quantity, email, shipping_country, shipping_address, shipping_postal_code, shipping_city, shipping_province]):
                return render_template(
                    'order_form.html',
                    products=products,
                    error="Tous les champs sont obligatoires."
                ), 422

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
            # Calcul du prix de livraison
            total_weight = product.weight * quantity
            try:
                shipping_price = calculate_shipping_price(total_weight)
            except Exception:
                shipping_price = 0

            # Calcul du total avec taxes
            try:
                subtotal = total_price + shipping_price
                total_price_tax = calculate_total_with_tax(subtotal, shipping_province)
            except Exception:
                total_price_tax = total_price + shipping_price

            order = Order.create(
                product_id=product.id,
                quantity=quantity,
                total_price=total_price,
                total_price_tax=total_price_tax,
                email=email,
                shipping_country=shipping_country,
                shipping_address=shipping_address,
                shipping_postal_code=shipping_postal_code,
                shipping_city=shipping_city,
                shipping_province=shipping_province,
                shipping_price=shipping_price
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

    @app.route('/ui/order/<int:order_id>/payment', methods=['GET', 'POST'])
    def ui_payment_form(order_id):
        try:
            order = Order.get_by_id(order_id)
            product = Product.get_by_id(order.product_id)
        except (Order.DoesNotExist, Product.DoesNotExist):
            return "Commande introuvable.", 404

        if order.paid:
            return render_template(
                'payment_form.html',
                order=order,
                product=product,
                error="La commande a déjà été payée."
            ), 422

        if not has_complete_customer_information(order):
            return render_template(
                'payment_form.html',
                order=order,
                product=product,
                error="Les informations client sont requises avant le paiement."
            ), 422

        if request.method == 'POST':
            credit_card_info = {
                "name": request.form.get('name', '').strip(),
                "number": request.form.get('number', '').strip(),
                "expiration_year": request.form.get('expiration_year', '').strip(),
                "expiration_month": request.form.get('expiration_month', '').strip(),
                "cvv": request.form.get('cvv', '').strip(),
            }

            if not all(credit_card_info.values()):
                return render_template(
                    'payment_form.html',
                    order=order,
                    product=product,
                    error="Tous les champs de carte de crédit sont obligatoires."
                ), 422

            payment_error = process_payment(order, credit_card_info)
            if payment_error is not None:
                response, status_code = payment_error
                error_payload = response.get_json(silent=True) if hasattr(response, 'get_json') else {}
                return render_template(
                    'payment_form.html',
                    order=order,
                    product=product,
                    error=extract_error_name(error_payload)
                ), status_code

            return redirect(url_for('ui_order_confirmation', order_id=order.id))

        return render_template('payment_form.html', order=order, product=product)


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
