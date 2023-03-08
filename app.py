from pathlib import Path

from flask import Flask, jsonify, render_template, request

from database import db
from models import Product, Order, ProductsOrder

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.instance_path = Path(".").resolve()
db.init_app(app)


@app.route("/")
def home():
    data = Product.query.all()
    return render_template("index.html", products=data)


@app.route("/api/product/<string:name>", methods=["GET"])
def api_get_product(name):
    inventory = Product.query.all()
    names = []
    for product in inventory:
        names.append(product.name)
        if name == product.name:
            product_json = product.to_dict()
            return jsonify(product_json)
    if name not in names:
        return (
            f"{name} is not available", 404,
        )

@app.route("/api/product", methods=["POST"])
def api_create_product():
    data = request.json
    # Check all data is provided
    for key in ("name", "price", "quantity"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400

    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        # Make sure they are positive
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )

    product = Product(
        name=data["name"],
        price=price,
        quantity=quantity,
    )
    db.session.add(product)
    db.session.commit()
    return "Item added to the database"

@app.route("/api/product/<string:name>", methods=["DELETE"])
def api_delete_product(name):
    product = db.session.get(Product, name.lower())
    db.session.delete(product)
    db.session.commit()
    return 'deleted item'

@app.route("/api/product/<string:name>", methods=["PUT"])
def api_update_product(name):
    data = request.json
    for key in ("price", "quantity"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400
    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        # Make sure they are positive
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )
    product = db.session.get(Product, name.lower())
    product.price = price
    product.quantity = quantity
    db.session.commit()
    return "Successfully updated"
    
@app.route("/api/order/<int:order_id>", methods=["GET"])
def api_get_order(order_id):
    order = db.session.get(Order, order_id)
    products_order = db.session.query(ProductsOrder).filter(ProductsOrder.order_id == order_id).all()
    inventory = Product.query.all()
    price = 0
    all_products = []
    for product in products_order:
        for inv_prod in inventory:
            if product.product_name == inv_prod.name:
                price += (inv_prod.price * product.quantity)
        if product.order_id == order_id:
            all_products.append(
                {
                "name": product.product_name,
                "quantity": product.quantity
                }
            )
    formatted_price = "{:.2f}".format(price)
    order_json = {
        "customer_name": order.name,
        "customer_address": order.address,
        "products": all_products,
        "price": formatted_price
    }
    return jsonify(order_json)

@app.route("/api/order", methods=["POST"])
def api_create_order():
    data = request.json
    inventory = Product.query.all()
    inv_list = []
    for inv_prod in inventory:
        inv_list.append(inv_prod.name)

    for item in data["products"]:
        if item["name"] not in inv_list:
            return (
                "Invalid values: items not in inventory", 400,
            )
        if type(item["quantity"]) != int or item["quantity"] <= 0:
            return (
                "Invalid number of items", 400,
            )
    o = Order(name=data["customer_name"], address=data["customer_address"])
    db.session.add(o)
    db.session.commit()
    for item in inv_list:
        for ord_prod in data["products"]:
            if item == ord_prod["name"]:
                add_item = db.session.get(Product, item)
                association = ProductsOrder(product=add_item, order=o, quantity=ord_prod["quantity"])
                db.session.add(association)
    db.session.commit()
    return "Successfully created"

@app.route("/api/order/<int:order_id>", methods=["PUT"])
def api_process_order(order_id):
    try:
        data = request.json
        keys = ["process"]
        for status in keys:
            if status not in data:
                raise ValueError
    except:
        return (
            "Invalid input", 400,
        )
    
    inventory = Product.query.all()
    order = db.session.get(Order, order_id)
    products_order = db.session.query(ProductsOrder).filter(ProductsOrder.order_id == order_id).all()
    
    if not data["process"] or order.completed:
        return 'nothing to be done here'
    
    list_products_order = []
    price = 0
    for ord_prod in products_order:
        for product in inventory:
            if ord_prod.product_name == product.name:
                if ord_prod.quantity > product.quantity:
                    ord_prod.quantity = product.quantity
                    db.session.commit()
                product.quantity -= ord_prod.quantity
                price += product.price * ord_prod.quantity
        order.completed = True
    db.session.commit()
    for ord_prod in products_order:
        list_products_order.append({
            "name": ord_prod.product_name,
            "quantity": ord_prod.quantity
        })
    formatted_price = "{:.2f}".format(price)
    order_json = {
        "customer_name": order.name,
        "customer_address": order.address,
        "products": list_products_order,
        "price": formatted_price
    }
    return jsonify(order_json)


if __name__ == "__main__":
    app.run(debug=True)
