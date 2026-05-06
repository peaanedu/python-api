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
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price NUMERIC(10,2) NOT NULL
        );
    """)

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM products;")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute("""
            INSERT INTO products (name, price)
            VALUES
            ('Laptop', 850),
            ('Firewall', 1200),
            ('Switch Cisco', 950);
        """)
        conn.commit()

    cur.close()
    conn.close()


@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "service": "products-service",
        "status": "running"
    })


@app.route("/products", methods=["GET"])
def get_products():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, price FROM products ORDER BY id;")
    rows = cur.fetchall()

    products = []

    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "price": float(row[2])
        })

    cur.close()
    conn.close()

    return jsonify(products)


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, price FROM products WHERE id=%s;",
        (product_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return jsonify({
            "id": row[0],
            "name": row[1],
            "price": float(row[2])
        })

    return jsonify({"error": "Product not found"}), 404


@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()

    name = data.get("name")
    price = data.get("price")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO products (name, price)
        VALUES (%s, %s)
        RETURNING id;
        """,
        (name, price)
    )

    product_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "id": product_id,
        "name": name,
        "price": price
    }), 201


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json()

    name = data.get("name")
    price = data.get("price")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE products
        SET name=%s, price=%s
        WHERE id=%s;
        """,
        (name, price, product_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "message": "Product updated",
        "id": product_id
    })


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM products WHERE id=%s;",
        (product_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "message": "Product deleted",
        "id": product_id
    })


if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )