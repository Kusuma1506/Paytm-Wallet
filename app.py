from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__)

CORS(app)


# DATABASE
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# CREATE TABLES
def create_tables():

    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        balance INTEGER
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount INTEGER
    )
    """)

    conn.commit()
    conn.close()


# HOME
@app.route("/")
def home():
    return render_template("index.html")


# CREATE USER
@app.route("/create-user", methods=["POST"])
def create_user():

    try:

        data = request.get_json()

        name = data["name"]
        balance = data["balance"]

        conn = get_db()

        existing = conn.execute(
            "SELECT * FROM users WHERE name=?",
            (name,)
        ).fetchone()

        if existing:

            return jsonify({
                "success": False,
                "error": "Username already exists"
            })

        conn.execute(
            "INSERT INTO users(name,balance) VALUES(?,?)",
            (name, balance)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "User Created Successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# CHECK BALANCE
@app.route("/balance/<name>", methods=["GET"])
def check_balance(name):

    try:

        conn = get_db()

        user = conn.execute(
            "SELECT balance FROM users WHERE name=?",
            (name,)
        ).fetchone()

        conn.close()

        if user is None:

            return jsonify({
                "success": False,
                "error": "User Not Found"
            })

        return jsonify({
            "success": True,
            "balance": user["balance"]
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# SEND MONEY
@app.route("/send-money", methods=["POST"])
def send_money():

    try:

        data = request.get_json()

        sender = data["sender"]
        receiver = data["receiver"]
        amount = int(data["amount"])

        conn = get_db()

        sender_data = conn.execute(
            "SELECT balance FROM users WHERE name=?",
            (sender,)
        ).fetchone()

        receiver_data = conn.execute(
            "SELECT balance FROM users WHERE name=?",
            (receiver,)
        ).fetchone()

        if sender_data is None:
            return jsonify({
                "success": False,
                "error": "Sender not found"
            })

        if receiver_data is None:
            return jsonify({
                "success": False,
                "error": "Receiver not found"
            })

        if sender_data["balance"] < amount:
            return jsonify({
                "success": False,
                "error": "Insufficient balance"
            })

        # deduct
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE name=?",
            (amount, sender)
        )

        # add
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE name=?",
            (amount, receiver)
        )

        # transaction
        conn.execute(
            "INSERT INTO transactions(sender,receiver,amount) VALUES(?,?,?)",
            (sender, receiver, amount)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Money Sent Successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# TRANSACTIONS
@app.route("/transactions", methods=["GET"])
def transactions():

    try:

        conn = get_db()

        tx = conn.execute(
            "SELECT * FROM transactions"
        ).fetchall()

        conn.close()

        result = []

        for t in tx:
            result.append(dict(t))

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# RUN
if __name__ == "__main__":

    create_tables()

    app.run(host="0.0.0.0", port=5000)
