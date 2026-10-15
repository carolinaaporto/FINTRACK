from datetime import date, datetime
import math
from pathlib import Path
import sqlite3

from flask import Flask, flash, redirect, render_template, request, url_for


app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DATABASE = Path(__file__).with_name("fintrack.db")
CATEGORIES = [
    "Salary",
    "Freelance",
    "Housing",
    "Food",
    "Transport",
    "Utilities",
    "Health",
    "Entertainment",
    "Other",
]


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT ''
            )
            """
        )


def get_transaction_values(form):
    kind = form.get("kind", "")
    category = form.get("category", "")
    transaction_date = form.get("transaction_date", "")
    note = form.get("note", "").strip()

    try:
        amount = float(form.get("amount", ""))
    except ValueError:
        return None, "Enter a valid amount."

    if kind not in ("income", "expense"):
        return None, "Choose income or expense."
    if category not in CATEGORIES:
        return None, "Choose a category from the list."
    if not math.isfinite(amount) or amount <= 0:
        return None, "The amount must be greater than zero."
    try:
        datetime.strptime(transaction_date, "%Y-%m-%d")
    except ValueError:
        return None, "Choose a valid date."

    return (kind, amount, category, transaction_date, note), None


def get_monthly_spending():
    today = date.today()
    months = []
    for months_ago in range(5, -1, -1):
        month_number = today.month - months_ago
        year = today.year + (month_number - 1) // 12
        month_number = (month_number - 1) % 12 + 1
        months.append(date(year, month_number, 1))

    first_month = months[0].strftime("%Y-%m")
    last_month = months[-1].strftime("%Y-%m")
    with get_db_connection() as connection:
        totals = connection.execute(
            """
            SELECT substr(transaction_date, 1, 7) AS month, SUM(amount) AS total
            FROM transactions
            WHERE kind = 'expense' AND month >= ? AND month <= ?
            GROUP BY month
            """,
            (first_month, last_month),
        ).fetchall()

    totals_by_month = {row["month"]: row["total"] for row in totals}
    chart = [
        {"label": month.strftime("%b"), "amount": totals_by_month.get(month.strftime("%Y-%m"), 0)}
        for month in months
    ]
    chart_max = max((month["amount"] for month in chart), default=0)
    return chart, chart_max


@app.route("/")
def index():
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    category = request.args.get("category", "")

    conditions = []
    values = []
    if start_date:
        conditions.append("transaction_date >= ?")
        values.append(start_date)
    if end_date:
        conditions.append("transaction_date <= ?")
        values.append(end_date)
    if category in CATEGORIES:
        conditions.append("category = ?")
        values.append(category)

    query = "SELECT * FROM transactions"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY transaction_date DESC, id DESC"

    with get_db_connection() as connection:
        transactions = connection.execute(query, values).fetchall()
        totals = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN kind = 'income' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN kind = 'expense' THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
            """
        ).fetchone()

    chart, chart_max = get_monthly_spending()
    return render_template(
        "index.html",
        transactions=transactions,
        categories=CATEGORIES,
        start_date=start_date,
        end_date=end_date,
        selected_category=category,
        income=totals["income"],
        expenses=totals["expenses"],
        balance=totals["income"] - totals["expenses"],
        chart=chart,
        chart_max=chart_max,
        today=date.today().isoformat(),
    )


@app.route("/transactions/add", methods=["POST"])
def add_transaction():
    transaction, error = get_transaction_values(request.form)
    if error:
        flash(error, "error")
        return redirect(url_for("index"))

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO transactions (kind, amount, category, transaction_date, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            transaction,
        )
    flash("Transaction added.", "success")
    return redirect(url_for("index"))


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    with get_db_connection() as connection:
        transaction = connection.execute(
            "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()

    if transaction is None:
        flash("That transaction could not be found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        values, error = get_transaction_values(request.form)
        if error:
            flash(error, "error")
            return render_template(
                "edit.html", transaction=request.form, transaction_id=transaction_id, categories=CATEGORIES
            )

        with get_db_connection() as connection:
            connection.execute(
                """
                UPDATE transactions
                SET kind = ?, amount = ?, category = ?, transaction_date = ?, note = ?
                WHERE id = ?
                """,
                (*values, transaction_id),
            )
        flash("Transaction updated.", "success")
        return redirect(url_for("index"))

    return render_template(
        "edit.html", transaction=transaction, transaction_id=transaction_id, categories=CATEGORIES
    )


@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
def delete_transaction(transaction_id):
    with get_db_connection() as connection:
        connection.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    flash("Transaction deleted.", "success")
    return redirect(url_for("index"))


initialize_database()


if __name__ == "__main__":
    app.run(debug=True)