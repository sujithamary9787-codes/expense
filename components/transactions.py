import streamlit as st

def show_transactions(df, role):
    st.subheader("Transactions")

    search = st.text_input("Search Category")

    if search:
        df = df[df["category"].str.contains(search, case=False)]

    st.dataframe(df)

    if role == "Admin":
        st.subheader("Add Transaction")

        date = st.date_input("Date")
        amount = st.number_input("Amount")
        category = st.text_input("Category")
        t_type = st.selectbox("Type", ["Income", "Expense"])

        if st.button("Add"):
            st.success("Transaction added (Demo Only)")