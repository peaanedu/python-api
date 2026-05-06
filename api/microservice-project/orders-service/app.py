from flask import Flask, jsonify, request
import psycopg2
import os
import time

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "products_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


def get_connection():
    for i in range(10):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print("Database connected successfully")
            return conn

        except psycopg2.OperationalError as e:
            print(f"Database not ready... retrying ({i+1}/10): {e}")
            time.sleep(5)

    raise Exception("Database connection failed after retries")

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM orders;")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute("""
            INSERT INTO orders (customer_id, product_id, quantity, status)
            VALUES
            (1, 1, 2, 'Completed'),
            (2, 2, 1, 'Pending');
        """)
        conn.commit()

    cur.close()
    conn.close()


@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "service": "orders-service",
        "status": "running"
    })


@app.route("/orders", methods=["GET"])
def get_orders():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, customer_id, product_id, quantity, status, created_at
        FROM orders
        ORDER BY id;
    """)

    rows = cur.fetchall()

    orders = []
    for row in rows:
        orders.append({
            "id": row[0],
            "customer_id": row[1],
            "product_id": row[2],
            "quantity": row[3],
            "status": row[4],
            "created_at": row[5].isoformat()
        })

    cur.close()
    conn.close()

    return jsonify(orders)


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, customer_id, product_id, quantity, status, created_at
        FROM orders
        WHERE id = %s;
    """, (order_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return jsonify({
            "id": row[0],
            "customer_id": row[1],
            "product_id": row[2],
            "quantity": row[3],
            "status": row[4],
            "created_at": row[5].isoformat()
        })

    return jsonify({"error": "Order not found"}), 404


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()

    customer_id = data.get("customer_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    status = data.get("status", "Pending")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders (customer_id, product_id, quantity, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at;
    """, (customer_id, product_id, quantity, status))

    result = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "id": result[0],
        "customer_id": customer_id,
        "product_id": product_id,
        "quantity": quantity,
        "status": status,
        "created_at": result[1].isoformat()
    }), 201


@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    data = request.get_json()

    customer_id = data.get("customer_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    status = data.get("status", "Pending")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET customer_id=%s,
            product_id=%s,
            quantity=%s,
            status=%s
        WHERE id=%s;
    """, (customer_id, product_id, quantity, status, order_id))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "message": "Order updated",
        "id": order_id
    })


@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM orders WHERE id=%s;", (order_id,))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "message": "Order deleted",
        "id": order_id
    })


if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )