import streamlit as st
from data import get_transactions
from utils import calculate_summary

from components.summary_cards import show_summary
from components.charts import show_balance_trend, show_category_chart
from components.transactions import show_transactions
from components.insights import show_insights

st.set_page_config(page_title="Finance Dashboard", layout="wide")

st.title("Finance Dashboard")

# Role switcher
role = st.sidebar.selectbox("Select Role", ["Viewer", "Admin"])

# Load data
df = get_transactions()

# Summary
balance, income, expense = calculate_summary(df)
show_summary(balance, income, expense)

st.divider()

# Charts
col1, col2 = st.columns(2)
with col1:
    show_balance_trend(df)

with col2:
    show_category_chart(df)

st.divider()

# Transactions
show_transactions(df, role)

st.divider()

# Insights
show_insights(df)