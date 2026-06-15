import streamlit as st
import pandas as pd
import psycopg2


if "user" not in st.session_state or st.session_state.user is None:
    st.warning(" Please login first from the main page")
    st.stop()


def get_connection():
    return psycopg2.connect(
        user='postgres',
        host='localhost',
        database='sales_intelligence_hub',
        port='5432',
        password='******'
    )

name      = st.session_state.user["username"]
branch_id = st.session_state.user["branch_id"]

st.title("Query Center")
st.divider()

# queries
BASIC_QUERIES = {
    "Retrieve all records from the customer_sales table":       "SELECT * FROM CUSTOMER_SALES",
    "Retrive all records from branches table":                  "SELECT * FROM BRANCHES",
    "Retrieve all records from the payment_splits table.":      "SELECT * FROM PAYMENT_SPLITS",
    "Display all records with status = 'open'":                 "SELECT * FROM CUSTOMER_SALES WHERE status = 'Open'"
}

AGGREGATE_QUERIES = {
    "Calculate the total gross sales across all branches":      "SELECT SUM(gross_sales) from customer_sales",
    "Calculate the total received amount across all sales":     "SELECT SUM(received_amount) from customer_sales",
    "calculate the total pending amount across all sales":      "SELECT SUM(pending_amount) from customer_sales",
    "Count the total number of sales per branch":               "SELECT count(gross_sales) from customer_sales GROUP BY gross_sales"
}

JOIN_BASED_QUERIES = {
    "Retrieve sales details along with the branch name.":       "SELECT customer_sales.*, branches.branch_name FROM customer_sales JOIN branches ON customer_sales.branch_id = branches.branch_id",
    "Show branch wise total gross sales":                       "SELECT branches.*, sum(customer_sales.gross_sales) FROM branches JOIN customer_sales ON branches.branch_id = customer_sales.branch_id GROUP BY branches.branch_id ORDER BY branches.branch_id ASC",
    "Display sales along with payment method used.":            "SELECT customer_sales.*, STRING_AGG(payment_splits.payment_method, ', ') AS payment_methods FROM customer_sales JOIN payment_splits ON customer_sales.sale_id = payment_splits.sale_id GROUP BY customer_sales.sale_id ORDER BY sale_id ASC",
    "Retrieve sales along with branch admin name.":             "SELECT customer_sales.*, branches.branch_admin_name FROM customer_sales JOIN branches ON customer_sales.branch_id = branches.branch_id"
}

FINANCIAL_TRACKING_QUERIES = {
    "Find sales where the pending amount is greater than 5000.":"SELECT * FROM customer_sales WHERE pending_amount > 5000",
    "Retrieve top 3 highest gross sales.":                      "SELECT * FROM customer_sales ORDER BY gross_sales DESC LIMIT 3",
    "Calculate payment method-wise total collection.":          "SELECT sum(amount_paid) as Total_Amount, payment_method FROM payment_splits GROUP BY payment_method",
}

# 
def append_branch_filter(query, branch_id):
    """Safely appends branch_id filter without breaking existing WHERE/GROUP BY clauses."""
    q = query.strip().rstrip(";")
    q_upper = q.upper()

    if "GROUP BY" in q_upper:
        # Already has HAVING?
        if "HAVING" in q_upper:
            return q + f" AND branch_id = {branch_id}"
        else:
            return q + f" HAVING branch_id = {branch_id}"
    elif "WHERE" in q_upper:
        # Already has WHERE — append with AND
        return q + f" AND branch_id = {branch_id}"
    else:
        return q + f" WHERE branch_id = {branch_id}"


def run_preset_query(query, branch_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if branch_id != 0:
            query = append_branch_filter(query, branch_id)
        cur.execute(query)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        return cols, rows
    finally:
        cur.close()
        conn.close()

# 
def display_query_result(query_dict, selected_key):
    """Runs query and shows result or a friendly message — never a raw error."""
    try:
        cols, rows = run_preset_query(query_dict[selected_key], branch_id)
        if not rows:
            st.info("ℹ️ No data found for your branch.")
            return
        df = pd.DataFrame(rows, columns=cols)
        st.success(f"✅ {len(df)} rows returned")
        st.dataframe(df, use_container_width=True)
    except psycopg2.errors.UndefinedColumn:
        st.warning("⚠️ You don't have access to view this report.")
    except psycopg2.OperationalError:
        st.warning("⚠️ Unable to connect to the database. Please try again later.")
    except Exception:
        st.warning("⚠️ This report is not available for your branch. Please contact your admin.")



st.subheader("Basic Queries")
basic_selected = st.selectbox("Select a question", list(BASIC_QUERIES.keys()), key="basic")
if st.button("Run Basic Query"):
    display_query_result(BASIC_QUERIES, basic_selected)

st.divider()

st.subheader("Aggregate Queries")
agg_selected = st.selectbox("Select a question", list(AGGREGATE_QUERIES.keys()), key="aggregate")
if st.button("Run Aggregate Query"):
    display_query_result(AGGREGATE_QUERIES, agg_selected)

st.divider()

st.subheader("Join Based Queries")
join_selected = st.selectbox("Select a question", list(JOIN_BASED_QUERIES.keys()), key="join")
if st.button("Run Join Based Query"):
    display_query_result(JOIN_BASED_QUERIES, join_selected)

st.divider()

st.subheader("Financial Tracking Queries")
fin_selected = st.selectbox("Select a question", list(FINANCIAL_TRACKING_QUERIES.keys()), key="financial")
if st.button("Run Financial Tracking Query"):
    display_query_result(FINANCIAL_TRACKING_QUERIES, fin_selected)

st.divider()

