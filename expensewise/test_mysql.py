# ExpenseWise uses SQLite, not MySQL.
# This file is kept only because the original project structure contained it.
# Run the application with:
#     python app.py

import sqlite3

try:
    conn = sqlite3.connect("expensewise.db")
    print("SQLite database connection successful.")
    conn.close()
except Exception as e:
    print("Database connection failed:", e)
