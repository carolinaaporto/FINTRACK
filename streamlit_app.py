from datetime import date
import html

import streamlit as st

from fintrack_data import (
    CATEGORIES,
    get_db_connection,
    get_monthly_spending,
    get_transaction_values,
    initialize_database,
)


st.set_page_config(page_title="FinTrack | Personal finances", page_icon="🌿", layout="wide")
initialize_database()

st.markdown(
    """
    <style>
    :root {
        --ink: #1d2b24;
        --muted: #78857d;
        --line: #e7ebe5;
        --green: #2e694d;
        --green-deep: #1d4533;
        --green-soft: #e8f1e9;
        --red: #bd6658;
        --red-soft: #f8ece9;
    }
    .stApp {
        background:
            radial-gradient(ellipse at 85% 0%, rgba(226, 235, 222, .55), transparent 34rem),
            #f6f7f3;
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: rgba(250, 251, 248, .84); }
    [data-testid="stMainBlockContainer"] { max-width: 1120px; padding-top: 2rem; }
    [data-testid="stToolbar"], footer { visibility: hidden; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -.6px; }
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.25rem !important; }
    .brand {
        display: flex;
        align-items: center;
        gap: 11px;
        color: var(--ink);
        font-family: Manrope, "DM Sans", sans-serif;
        font-size: 17px;
        font-weight: 800;
        letter-spacing: -.5px;
    }
    .brand-mark {
        width: 34px;
        height: 34px;
        display: inline-grid;
        place-items: center;
        border-radius: 11px;
        background: var(--green-deep);
        color: white;
        box-shadow: 0 4px 10px rgba(29, 69, 51, .16);
    }
    .eyebrow {
        margin: 0 0 7px;
        color: var(--green);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
    }
    .summary-card {
        position: relative;
        min-height: 145px;
        padding: 21px 23px;
        overflow: hidden;
        border: 1px solid rgba(226, 232, 224, .9);
        border-radius: 15px;
        background: rgba(255, 255, 255, .9);
        box-shadow: 0 12px 32px rgba(34, 52, 40, .045);
    }
    .summary-card::after, .summary-card::before {
        position: absolute;
        right: -27px;
        bottom: -50px;
        width: 132px;
        height: 132px;
        border: 1px solid rgba(46, 105, 77, .07);
        border-radius: 50%;
        content: "";
    }
    .summary-card::before {
        right: -7px;
        bottom: -31px;
        width: 92px;
        height: 92px;
    }
    .summary-label { color: var(--muted); font-size: 12px; font-weight: 600; }
    .summary-value {
        position: relative;
        z-index: 1;
        margin: 16px 0 3px;
        color: var(--ink);
        font-family: Manrope, "DM Sans", sans-serif;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -1.2px;
        line-height: 1.15;
        font-variant-numeric: tabular-nums;
    }
    .summary-note { color: #909b93; font-size: 11px; }
    .balance-card {
        border-color: var(--green-deep);
        background: linear-gradient(135deg, #234f39, #1d4533);
    }
    .balance-card .summary-label, .balance-card .summary-note { color: rgba(255,255,255,.67); }
    .balance-card .summary-value { color: white; }
    .balance-card::after, .balance-card::before { border-color: rgba(255,255,255,.08); }
    [data-testid="stForm"], [data-testid="stDataFrame"], [data-testid="stTable"] {
        border-color: var(--line);
        border-radius: 13px;
    }
    [data-testid="stBaseButton-primary"] {
        border-color: var(--green-deep);
        background: var(--green-deep);
    }
    [data-testid="stBaseButton-primary"]:hover {
        border-color: #173a2a;
        background: #173a2a;
    }
    [data-testid="stWidgetLabel"] p { color: #59665e; font-size: 12px; font-weight: 600; }
    .transaction-table-wrap {
        overflow-x: auto;
        border: 1px solid var(--line);
        border-radius: 15px;
        background: white;
        box-shadow: 0 12px 32px rgba(34, 52, 40, .045);
    }
    table.transaction-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        font-family: "DM Sans", sans-serif;
        font-size: 12px;
    }
    .transaction-table th {
        height: 44px;
        padding: 0 15px;
        background: #f8faf7;
        color: #89958d;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .4px;
        text-transform: uppercase;
    }
    .transaction-table td {
        height: 54px;
        padding: 0 15px;
        border-top: 1px solid #eef1ed;
        color: #59665e;
        white-space: nowrap;
    }
    .transaction-table td:first-child { color: var(--ink); font-weight: 600; }
    .transaction-table .positive { color: var(--green); font-weight: 700; }
    .transaction-table .negative { color: var(--red); font-weight: 700; }
    .transaction-table .category {
        padding: 5px 9px;
        border-radius: 999px;
        background: #f2f5f1;
        color: #617067;
        font-size: 10px;
    }
    .empty-state {
        padding: 22px;
        border: 1px dashed #dce4da;
        border-radius: 13px;
        color: var(--muted);
        text-align: center;
    }
    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 2rem; }
        .summary-card { min-height: 125px; padding: 16px; }
        .summary-value { font-size: 25px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))

if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None

topbar_left, topbar_right = st.columns([1, 1])
with topbar_left:
    st.markdown(
        '<div class="brand"><span class="brand-mark">F</span> FinTrack</div>',
        unsafe_allow_html=True,
    )
with topbar_right:
    st.markdown(
        f'<div style="text-align:right;color:#78857d;padding-top:7px">{date.today():%b %d, %Y}</div>',
        unsafe_allow_html=True,
    )

st.write("")
heading_left, heading_right = st.columns([3, 1])
with heading_left:
    st.markdown('<p class="eyebrow">YOUR MONEY, IN FOCUS</p>', unsafe_allow_html=True)
    st.title("Overview")
    st.caption("A clear view of where your money goes.")
with heading_right:
    st.write("")
    st.write("")
    st.link_button("＋ Add transaction", "#add-transaction", type="primary", use_container_width=True)

with get_db_connection() as connection:
    totals = connection.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN kind = 'income' THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN kind = 'expense' THEN amount ELSE 0 END), 0) AS expenses
        FROM transactions
        """
    ).fetchone()

summary_columns = st.columns(3, gap="medium")
summary_items = [
    ("Total income", totals["income"], "All recorded income", ""),
    ("Total expenses", totals["expenses"], "All recorded spending", ""),
    ("Current balance", totals["income"] - totals["expenses"], "Income minus expenses", "balance-card"),
]
for column, (label, amount, note, card_class) in zip(summary_columns, summary_items):
    with column:
        st.markdown(
            f"""
            <section class="summary-card {card_class}">
                <div class="summary-label">● &nbsp;{label}</div>
                <div class="summary-value">${amount:,.2f}</div>
                <div class="summary-note">{note}</div>
            </section>
            """,
            unsafe_allow_html=True,
        )

st.write("")
chart_heading, chart_period = st.columns([3, 1])
with chart_heading:
    st.markdown('<p class="eyebrow">SPENDING TRENDS</p>', unsafe_allow_html=True)
    st.subheader("Monthly expenses")
with chart_period:
    st.caption("Last 6 months")

chart, _ = get_monthly_spending()
st.bar_chart(
    {"Month": [month["label"] for month in chart], "Expenses": [month["amount"] for month in chart]},
    x="Month",
    y="Expenses",
    color="#6e9a7a",
    height=230,
)

st.write("")
st.markdown('<p class="eyebrow">YOUR ACTIVITY</p>', unsafe_allow_html=True)
st.subheader("Transactions")

clear_column, _ = st.columns([1, 4])
with clear_column:
    if st.button("Clear filters", use_container_width=True):
        for filter_key in ("filter_start", "filter_end", "filter_category"):
            st.session_state.pop(filter_key, None)
        st.rerun()

filter_columns = st.columns([1, 1, 1.2])
with filter_columns[0]:
    start_date = st.date_input("From", value=None, key="filter_start")
with filter_columns[1]:
    end_date = st.date_input("To", value=None, key="filter_end")
with filter_columns[2]:
    selected_category = st.selectbox("Category", ["All categories", *CATEGORIES], key="filter_category")

if start_date and end_date and start_date > end_date:
    st.error("The start date must be on or before the end date.")

conditions = []
values = []
if start_date:
    conditions.append("transaction_date >= ?")
    values.append(start_date.isoformat())
if end_date:
    conditions.append("transaction_date <= ?")
    values.append(end_date.isoformat())
if selected_category != "All categories":
    conditions.append("category = ?")
    values.append(selected_category)

query = "SELECT * FROM transactions"
if conditions:
    query += " WHERE " + " AND ".join(conditions)
query += " ORDER BY transaction_date DESC, id DESC"
with get_db_connection() as connection:
    transactions = connection.execute(query, values).fetchall()

if transactions:
    rows = []
    for transaction in transactions:
        kind = transaction["kind"]
        description = html.escape(transaction["note"] or transaction["category"])
        category = html.escape(transaction["category"])
        transaction_date = html.escape(transaction["transaction_date"])
        amount_class = "positive" if kind == "income" else "negative"
        sign = "+" if kind == "income" else "−"
        rows.append(
            "<tr>"
            f"<td>{description}</td>"
            f"<td>{transaction_date}</td>"
            f'<td><span class="category">{category}</span></td>'
            f"<td>{kind.title()}</td>"
            f'<td class="{amount_class}" style="text-align:right">{sign}${transaction["amount"]:,.2f}</td>'
            "</tr>"
        )
    st.markdown(
        '<div class="transaction-table-wrap"><table class="transaction-table">'
        "<thead><tr><th>Transaction</th><th>Date</th><th>Category</th><th>Type</th>"
        '<th style="text-align:right">Amount</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="empty-state">No transactions match those filters. Add your first one below.</div>',
        unsafe_allow_html=True,
    )

st.write("")
st.markdown('<p class="eyebrow" id="add-transaction">KEEP IT UP TO DATE</p>', unsafe_allow_html=True)
st.subheader("Add a transaction")
with st.form("add_transaction", clear_on_submit=True):
    add_columns = st.columns(4)
    with add_columns[0]:
        add_kind = st.selectbox("Type", ["expense", "income"], format_func=str.title)
    with add_columns[1]:
        add_amount = st.number_input("Amount", min_value=0.01, value=0.01, step=1.0, format="%.2f")
    with add_columns[2]:
        add_category = st.selectbox("Category", CATEGORIES)
    with add_columns[3]:
        add_date = st.date_input("Date", value=date.today())
    add_note = st.text_input("Note (optional)", max_chars=120, placeholder="What was this for?")
    add_submitted = st.form_submit_button("Save transaction", type="primary")

if add_submitted:
    transaction_values, error = get_transaction_values(
        {
            "kind": add_kind,
            "amount": add_amount,
            "category": add_category,
            "transaction_date": add_date.isoformat(),
            "note": add_note,
        }
    )
    if error:
        st.error(error)
    else:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO transactions (kind, amount, category, transaction_date, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                transaction_values,
            )
        st.session_state.notice = "Transaction added."
        st.rerun()

if transactions:
    st.write("")
    with st.expander("Edit or delete a transaction"):
        transaction_by_id = {transaction["id"]: transaction for transaction in transactions}
        selected_id = st.selectbox(
            "Choose a transaction",
            list(transaction_by_id),
            format_func=lambda transaction_id: (
                f'{transaction_by_id[transaction_id]["transaction_date"]} · '
                f'{transaction_by_id[transaction_id]["category"]} · '
                f'${transaction_by_id[transaction_id]["amount"]:,.2f}'
            ),
        )
        selected_transaction = transaction_by_id[selected_id]
        with st.form(f"edit_transaction_{selected_id}"):
            edit_columns = st.columns(4)
            with edit_columns[0]:
                edit_kind = st.selectbox(
                    "Type",
                    ["expense", "income"],
                    index=["expense", "income"].index(selected_transaction["kind"]),
                    format_func=str.title,
                    key=f"edit_kind_{selected_id}",
                )
            with edit_columns[1]:
                edit_amount = st.number_input(
                    "Amount",
                    min_value=0.01,
                    value=float(selected_transaction["amount"]),
                    step=1.0,
                    format="%.2f",
                    key=f"edit_amount_{selected_id}",
                )
            with edit_columns[2]:
                edit_category = st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=CATEGORIES.index(selected_transaction["category"]),
                    key=f"edit_category_{selected_id}",
                )
            with edit_columns[3]:
                edit_date = st.date_input(
                    "Date",
                    value=date.fromisoformat(selected_transaction["transaction_date"]),
                    key=f"edit_date_{selected_id}",
                )
            edit_note = st.text_input(
                "Note (optional)",
                value=selected_transaction["note"],
                max_chars=120,
                key=f"edit_note_{selected_id}",
            )
            edit_submitted = st.form_submit_button("Save changes", type="primary")

        if edit_submitted:
            transaction_values, error = get_transaction_values(
                {
                    "kind": edit_kind,
                    "amount": edit_amount,
                    "category": edit_category,
                    "transaction_date": edit_date.isoformat(),
                    "note": edit_note,
                }
            )
            if error:
                st.error(error)
            else:
                with get_db_connection() as connection:
                    connection.execute(
                        """
                        UPDATE transactions
                        SET kind = ?, amount = ?, category = ?, transaction_date = ?, note = ?
                        WHERE id = ?
                        """,
                        (*transaction_values, selected_id),
                    )
                st.session_state.notice = "Transaction updated."
                st.rerun()

        if st.button("Delete selected transaction", key=f"delete_{selected_id}"):
            st.session_state.confirm_delete_id = selected_id
        if st.session_state.confirm_delete_id == selected_id:
            st.warning("Delete this transaction? This cannot be undone.")
            confirm_column, cancel_column = st.columns(2)
            with confirm_column:
                if st.button("Confirm delete", type="primary", key=f"confirm_delete_{selected_id}"):
                    with get_db_connection() as connection:
                        connection.execute("DELETE FROM transactions WHERE id = ?", (selected_id,))
                    st.session_state.confirm_delete_id = None
                    st.session_state.notice = "Transaction deleted."
                    st.rerun()
            with cancel_column:
                if st.button("Cancel", key=f"cancel_delete_{selected_id}"):
                    st.session_state.confirm_delete_id = None
                    st.rerun()

st.write("")
st.caption("FinTrack · Your finances, organized.")
