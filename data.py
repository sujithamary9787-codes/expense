import pandas as pd

def get_transactions():
    data = [
        {"date": "2026-03-01", "amount": 25000, "category": "Salary", "type": "Income"},
        {"date": "2026-03-03", "amount": 1200, "category": "Food", "type": "Expense"},
        {"date": "2026-03-05", "amount": 3000, "category": "Rent", "type": "Expense"},
        {"date": "2026-03-10", "amount": 5000, "category": "Freelance", "type": "Income"},
        {"date": "2026-03-12", "amount": 800, "category": "Transport", "type": "Expense"},
        {"date": "2026-03-15", "amount": 1500, "category": "Shopping", "type": "Expense"},
    ]

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df