# FinTrack

A small personal finance tracker built with Flask, SQLite, HTML, and CSS. It lets you record income and expenses, edit or remove them, filter by date and category, and see your balance and recent monthly spending.

## Run it locally

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install Flask:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   python app.py
   ```

4. Open http://127.0.0.1:5000 in your browser.

The SQLite database (`fintrack.db`) is created automatically the first time the app starts. Your transaction data stays in that local file.