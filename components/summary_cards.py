import streamlit as st

def show_summary(balance, income, expense):
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Balance", f"₹{balance}")
    col2.metric("Income", f"₹{income}")
    col3.metric("Expenses", f"₹{expense}")