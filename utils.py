def calculate_summary(df):
    income = df[df["type"] == "Income"]["amount"].sum()
    expense = df[df["type"] == "Expense"]["amount"].sum()
    balance = income - expense

    return balance, income, expense