import streamlit as st

def show_insights(df):
    st.subheader("Insights")

    expense_df = df[df["type"] == "Expense"]

    highest = expense_df.groupby("category")["amount"].sum().idxmax()
    total_expense = expense_df["amount"].sum()
    total_income = df[df["type"] == "Income"]["amount"].sum()

    col1, col2, col3 = st.columns(3)

    col1.info(f"Highest Spending: {highest}")
    col2.info(f"Total Expense: ₹{total_expense}")
    col3.info(f"Total Income: ₹{total_income}")