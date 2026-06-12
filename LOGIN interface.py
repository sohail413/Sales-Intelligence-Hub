import streamlit as st
import pandas as pd
import psycopg2

# ── 1. Database Connection ────────────────────────
def get_connection():
    return psycopg2.connect(
        user='postgres',
        host='localhost',
        database='sales_intelligence_hub',
        port='5432',
        password='sohail4'
    )

# ── 2. Users ──────────────────────────────────────
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
# ✅ Fix 1: branch_id are integers now, not strings like "0","1"

# ── 3. Fetch Data ─────────────────────────────────
def get_cust_data(table_name, branch_id):
    conn = get_connection()
    cur = conn.cursor()

    if branch_id == 0:  
        # ✅ Fix 2: use == not "is" for comparison
        cur.execute(f"SELECT * FROM {table_name} LIMIT 1000")
    else:
        cur.execute(f"SELECT * FROM {table_name} WHERE branch_id = %s LIMIT 1000", (branch_id,))

    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return col_names, rows

# ── 4. Session State ──────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ── 5. Page Title ─────────────────────────────────
st.title("WELCOME TO SALES INTELLIGENCE HUB")

st.info(" Hi Admins " \
"Sales Intelligence Hub  allows you to view sales data , edit data and to analyse the performance from the data. "\
 " you can access data through the menu in the left showing different modules"\
" DASHBOARD"  
" - QUERY CENTRE"
" - VIEW SALES DATA"       )

# ── 6. Login Form ─────────────────────────────────
if st.session_state.user is None:
    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):  
        # ✅ Fix 3: Login button is now INSIDE the if block
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.user = {
                "username":  username,
                "branch_id": user["branch_id"]
            }
            st.rerun()
        else:
            st.error("❌ Wrong username or password")

# ── 7. Dashboard ──────────────────────────────────
else:
    # ✅ Fix 4: Check username not USERS dict for role
    name      = st.session_state.user["username"]
    branch_id = st.session_state.user["branch_id"]

    if name == "superadmin":
        st.title(f" Super Admin — {name}")
        st.info(" You can see all branches")
    else:
        st.title(f" Admin Panel — {name}")
        st.info(f" You are viewing Branch ID: {branch_id}")

    st.divider()

   
    

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    