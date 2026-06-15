import streamlit as st
import pandas as pd
import psycopg2


def get_connection():
    return psycopg2.connect(
        user='postgres',
        host='localhost',
        database='sales_intelligence_hub',
        port='5432',
        password='******'
    )

def get_cust_data(table_name, branch_id):
    conn = get_connection()
    cur = conn.cursor()

    if branch_id == 0:
        cur.execute(f"SELECT * FROM {table_name} LIMIT 1000")
    else:
        cur.execute(f"SELECT * FROM {table_name} WHERE branch_id = %s LIMIT 1000", (branch_id,))

    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return col_names, rows


if "user" not in st.session_state:
    st.session_state.user = None


st.title("SALES DATA")

name      = st.session_state.user["username"]
branch_id = st.session_state.user["branch_id"]

if name == "superadmin":
    st.title(f"Super Admin — {name}")
    st.info("Welcome super admin")
    TABLES = ["customer_sales", "payment_splits", "branches"]  # ✅ All tables
else:
    st.title(f"Admin Panel — {name}")
    st.info(f"Welcome {name}, You are viewing Branch ID: {branch_id}")
    TABLES = ["customer_sales"]  # ✅ Restricted to one table

st.divider()

for table in TABLES:
    st.subheader(f"{table.upper()}")
    try:
        cols, rows = get_cust_data(table, branch_id)
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"No data found for branch {branch_id}")
    except Exception as e:
        st.error(f"Could not load {table}: {e}")

    st.divider()

if st.button("Logout"):
    st.session_state.user = None
    st.rerun()
