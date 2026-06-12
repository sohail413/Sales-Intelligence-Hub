import streamlit as st
import psycopg2

def get_connection():
    return psycopg2.connect(
        user='postgres',
        host='localhost',
        database='sales_intelligence_hub',
        port='5432',
        password='******'
    )

USERS = {
    "superadmin":       {"password": "super", "branch_id": 0},
    "admin_chennai":    {"password": "che", "branch_id": 1},
    "admin_bangalore":  {"password": "ban", "branch_id": 2},
    "admin_hyderabad":  {"password": "hyd", "branch_id": 3},
    "admin_delhi":      {"password": "del", "branch_id": 4},
    "admin_mumbai":     {"password": "mum", "branch_id": 5},
    "admin_pune":       {"password": "pun", "branch_id": 6},
    "admin_kolkata":    {"password": "kol", "branch_id": 7},
    "admin_ahmedabad":  {"password": "ahm", "branch_id": 8},
}

if "user" not in st.session_state:
    st.session_state.user = None

st.title("WELCOME TO SALES INTELLIGENCE HUB")

if st.session_state.user is None:
    st.subheader(" Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.user = {
                "username":  username,
                "branch_id": user["branch_id"]
            }
            st.rerun()
        else:
            st.error("❌ Wrong username or password")
else:
    st.success(f" Logged in as {st.session_state.user['username']}")
    st.info(" Use the sidebar to navigate to Dashboard or Query Center")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()
