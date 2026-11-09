from datetime import date, datetime
import math
from pathlib import Path
import sqlite3


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
    except (TypeError, ValueError):
        return None, "Enter a valid amount."

    if kind not in ("income", "expense"):
        return None, "Choose income or expense."
    if category not in CATEGORIES:
        return None, "Choose a category from the list."
    if not math.isfinite(amount) or amount <= 0:
        return None, "The amount must be greater than zero."
    try:
        datetime.strptime(transaction_date, "%Y-%m-%d")
    except (TypeError, ValueError):
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
