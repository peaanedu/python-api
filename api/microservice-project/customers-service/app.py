from flask import Flask, jsonify, request
import psycopg2
import os
import time

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

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
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM customers;")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute("""
            INSERT INTO customers (name, email, phone)
            VALUES
            ('Sokha', 'sokha@example.com', '012345678'),
            ('Dara', 'dara@example.com', '098765432');
        """)
        conn.commit()

    cur.close()
    conn.close()


@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "service": "customers-service",
        "status": "running"
    })


@app.route("/customers", methods=["GET"])
def get_customers():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, email, phone, created_at
        FROM customers
        ORDER BY id;
    """)

    rows = cur.fetchall()

    customers = []
    for row in rows:
        customers.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3],
            "created_at": row[4].isoformat()
        })

    cur.close()
    conn.close()

    return jsonify(customers)


@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, email, phone, created_at
        FROM customers
        WHERE id = %s;
    """, (customer_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return jsonify({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3],
            "created_at": row[4].isoformat()
        })

    return jsonify({"error": "Customer not found"}), 404


@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO customers (name, email, phone)
        VALUES (%s, %s, %s)
        RETURNING id, created_at;
    """, (name, email, phone))

    result = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "id": result[0],
        "name": name,
        "email": email,
        "phone": phone,
        "created_at": result[1].isoformat()
    }), 201


@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE customers
        SET name=%s,
            email=%s,
            phone=%s
        WHERE id=%s;
    """, (name, email, phone, customer_id))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "message": "Customer updated",
        "id": customer_id
    })


@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM customers WHERE id=%s;", (customer_id,))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "message": "Customer deleted",
        "id": customer_id
    })


if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )