from flask import Flask, jsonify, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# -----------------------------
# Products Microservice
# -----------------------------
products_app = Flask("products_service")

products = [
    {"id": 1, "name": "Laptop", "price": 850},
    {"id": 2, "name": "Firewall", "price": 1200},
]

@products_app.route("/products", methods=["GET"])
def get_products():
    return jsonify(products)

@products_app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    return jsonify(product) if product else (jsonify({"error": "Product not found"}), 404)


# -----------------------------
# Orders Microservice
# -----------------------------
orders_app = Flask("orders_service")

orders = [
    {"id": 1, "customer_id": 1, "product_id": 1, "quantity": 2},
    {"id": 2, "customer_id": 2, "product_id": 2, "quantity": 1},
]

@orders_app.route("/orders", methods=["GET"])
def get_orders():
    return jsonify(orders)

@orders_app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    new_order = {
        "id": len(orders) + 1,
        "customer_id": data["customer_id"],
        "product_id": data["product_id"],
        "quantity": data["quantity"],
    }
    orders.append(new_order)
    return jsonify(new_order), 201


# -----------------------------
# Customers Microservice
# -----------------------------
customers_app = Flask("customers_service")

customers = [
    {"id": 1, "name": "Sokha", "email": "sokha@example.com"},
    {"id": 2, "name": "Dara", "email": "dara@example.com"},
]

@customers_app.route("/customers", methods=["GET"])
def get_customers():
    return jsonify(customers)

@customers_app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = next((c for c in customers if c["id"] == customer_id), None)
    return jsonify(customer) if customer else (jsonify({"error": "Customer not found"}), 404)


# -----------------------------
# API Gateway
# -----------------------------
gateway_app = Flask("api_gateway")

@gateway_app.route("/")
def home():
    return jsonify({
        "message": "API Gateway is running",
        "services": {
            "products": "/products",
            "orders": "/orders",
            "customers": "/customers"
        }
    })


# Mount microservices under API Gateway
application = DispatcherMiddleware(gateway_app, {
    "/products-service": products_app,
    "/orders-service": orders_app,
    "/customers-service": customers_app,
})


if __name__ == "__main__":
    run_simple(
        hostname="0.0.0.0",
        port=5000,
        application=application,
        use_debugger=True,
        use_reloader=True
    )