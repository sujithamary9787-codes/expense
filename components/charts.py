import streamlit as st
import plotly.express as px

def show_balance_trend(df):
    trend = df.groupby("date")["amount"].sum().cumsum().reset_index()
    fig = px.line(trend, x="date", y="amount", title="Balance Trend")
    st.plotly_chart(fig, use_container_width=True)

def show_category_chart(df):
    expense_df = df[df["type"] == "Expense"]
    category = expense_df.groupby("category")["amount"].sum().reset_index()

    fig = px.pie(category, values="amount", names="category", title="Spending Breakdown")
    st.plotly_chart(fig, use_container_width=True)