import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

# ── Guard ─────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning(" Please login first from the main page")
    st.stop()

# ── Connection ────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        user='postgres',
        host='localhost',
        database='sales_intelligence_hub',
        port='5432',
        password='sohail4'
    )

def run_query(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params or [])
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=cols)

# ── User Info ─────────────────────────────────────
name      = st.session_state.user["username"]
branch_id = st.session_state.user["branch_id"]
is_super  = (name == "superadmin")

# ── Page Header ───────────────────────────────────
st.title(" Insights & Reporting")
if is_super:
    st.info("Super Admin — Viewing ALL branches")
else:
    st.info(f" Admin — Viewing your branch only (Branch ID: {branch_id})")

st.divider()

# ══════════════════════════════════════════════════
# 1. OVERALL BUSINESS REVENUE
# ══════════════════════════════════════════════════
st.subheader("  Overall Business Revenue")

try:
    if is_super:
        df_revenue = run_query("""
            SELECT
                COUNT(*)                AS total_orders,
                SUM(gross_sales)        AS total_revenue,
                SUM(received_amount)    AS total_received,
                SUM(gross_sales - received_amount) AS total_pending
            FROM customer_sales
        """)
    else:
        df_revenue = run_query("""
            SELECT
                COUNT(*)                AS total_orders,
                SUM(gross_sales)        AS total_revenue,
                SUM(received_amount)    AS total_received,
                SUM(gross_sales - received_amount) AS total_pending
            FROM customer_sales
            WHERE branch_id = %s
        """, [branch_id])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(" Total Orders",   int(df_revenue["total_orders"][0]))
    col2.metric(" Total Revenue",  f"₹{float(df_revenue['total_revenue'][0]):,.2f}")
    col3.metric(" Total Received", f"₹{float(df_revenue['total_received'][0]):,.2f}")
    col4.metric(" Total Pending",  f"₹{float(df_revenue['total_pending'][0]):,.2f}")

except Exception as e:
    st.error(f"❌ Revenue error: {e}")

st.divider()

# ══════════════════════════════════════════════════
# 2. BRANCH-WISE SALES COMPARISON
# ══════════════════════════════════════════════════
st.subheader("🏢 Branch-wise Sales Comparison")

try:
    if is_super:
        df_branch = run_query("""
            SELECT
                b.branch_name,
                COUNT(cs.sale_id)               AS total_orders,
                SUM(cs.gross_sales)             AS total_sales,
                SUM(cs.received_amount)         AS received,
                SUM(cs.gross_sales - cs.received_amount) AS pending
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            GROUP BY b.branch_name
            ORDER BY total_sales DESC
        """)
    else:
        df_branch = run_query("""
            SELECT
                b.branch_name,
                COUNT(cs.sale_id)               AS total_orders,
                SUM(cs.gross_sales)             AS total_sales,
                SUM(cs.received_amount)         AS received,
                SUM(cs.gross_sales - cs.received_amount) AS pending
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            WHERE cs.branch_id = %s
            GROUP BY b.branch_name
            ORDER BY total_sales DESC
        """, [branch_id])

    fig = px.bar(
        df_branch, x="branch_name", y="total_sales",
        color="branch_name", title="Total Sales by Branch",
        labels={"branch_name": "Branch", "total_sales": "Total Sales (₹)"},
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_branch, use_container_width=True)

except Exception as e:
    st.error(f"❌ Branch comparison error: {e}")

st.divider()

# ══════════════════════════════════════════════════
# 3. RECEIVED VS PENDING
# ══════════════════════════════════════════════════
st.subheader(" Total Received vs Total Pending")

try:
    if is_super:
        df_rp = run_query("""
            SELECT
                SUM(received_amount)                    AS received,
                SUM(gross_sales - received_amount)      AS pending
            FROM customer_sales
        """)
    else:
        df_rp = run_query("""
            SELECT
                SUM(received_amount)                    AS received,
                SUM(gross_sales - received_amount)      AS pending
            FROM customer_sales
            WHERE branch_id = %s
        """, [branch_id])

    received = float(df_rp["received"][0])
    pending  = float(df_rp["pending"][0])

    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(
            names=["Received", "Pending"],
            values=[received, pending],
            color_discrete_map={"Received":"#33cc2e", "Pending": " #e74c3c"},
            title="Received vs Pending"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        st.metric(" Total Received", f"₹{received:,.2f}")
        st.metric(" Total Pending",  f"₹{pending:,.2f}")

except Exception as e:
    st.error(f" Received vs Pending error: {e}")

st.divider()

# ══════════════════════════════════════════════════
# 4. PENDING COLLECTION PERCENTAGE
# ══════════════════════════════════════════════════
st.subheader(" Pending Collection Percentage")

try:
    if is_super:
        df_pct = run_query("""
            SELECT
                b.branch_name,
                ROUND(
                    SUM(cs.gross_sales - cs.received_amount) * 100.0
                    / NULLIF(SUM(cs.gross_sales), 0), 2
                ) AS pending_pct
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            GROUP BY b.branch_name
            ORDER BY pending_pct DESC
        """)
    else:
        df_pct = run_query("""
            SELECT
                b.branch_name,
                ROUND(
                    SUM(cs.gross_sales - cs.received_amount) * 100.0
                    / NULLIF(SUM(cs.gross_sales), 0), 2
                ) AS pending_pct
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            WHERE cs.branch_id = %s
            GROUP BY b.branch_name
            ORDER BY pending_pct DESC
        """, [branch_id])

    fig = px.bar(
        df_pct, x="branch_name", y="pending_pct",
        color="pending_pct", color_continuous_scale="Reds",
        title="Pending Collection % by Branch",
        labels={"branch_name": "Branch", "pending_pct": "Pending %"},
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f" Pending % error: {e}")

st.divider()

# ══════════════════════════════════════════════════
# 5. PAYMENT METHOD ANALYSIS
# ══════════════════════════════════════════════════
st.subheader(" Payment Method Analysis (Cash / UPI / Card)")

try:
    # payment_splits has no branch_id — join through customer_sales
    if is_super:
        df_pay = run_query("""
            SELECT
                ps.payment_method,
                COUNT(*)            AS total_transactions,
                SUM(ps.amount_paid) AS total_amount
            FROM payment_splits ps
            GROUP BY ps.payment_method
            ORDER BY total_amount DESC
        """)
    else:
        df_pay = run_query("""
            SELECT
                ps.payment_method,
                COUNT(*)            AS total_transactions,
                SUM(ps.amount_paid) AS total_amount
            FROM payment_splits ps
            JOIN customer_sales cs ON ps.sale_id = cs.sale_id
            WHERE cs.branch_id = %s
            GROUP BY ps.payment_method
            ORDER BY total_amount DESC
        """, [branch_id])

    col1, col2 = st.columns(2)
    with col1:
        fig_bar = px.bar(
            df_pay, x="payment_method", y="total_amount",
            color="payment_method", title="Amount by Payment Method",
            labels={"payment_method": "Method", "total_amount": "Amount (₹)"},
            text_auto=True
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        fig_pie = px.pie(
            df_pay, names="payment_method", values="total_transactions",
            title="Transactions by Payment Method"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.dataframe(df_pay, use_container_width=True)

except Exception as e:
    st.error(f" Payment method error: {e}")

st.divider()

# ══════════════════════════════════════════════════
# 6. SALES TRENDS & GROWTH
# ══════════════════════════════════════════════════
st.subheader(" Sales Trends & Growth")

try:
    if is_super:
        df_trend = run_query("""
            SELECT
                DATE_TRUNC('month', date::date) AS month,
                SUM(gross_sales)                AS total_sales,
                COUNT(*)                        AS total_orders
            FROM customer_sales
            GROUP BY month
            ORDER BY month
        """)
    else:
        df_trend = run_query("""
            SELECT
                DATE_TRUNC('month', date::date) AS month,
                SUM(gross_sales)                AS total_sales,
                COUNT(*)                        AS total_orders
            FROM customer_sales
            WHERE branch_id = %s
            GROUP BY month
            ORDER BY month
        """, [branch_id])

    df_trend["month"]    = pd.to_datetime(df_trend["month"])
    df_trend["growth_%"] = df_trend["total_sales"].pct_change() * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_trend["month"], y=df_trend["total_sales"],
        mode="lines+markers", name="Total Sales",
        line=dict(color="#3498db", width=3)
    ))
    fig.update_layout(
        title="Monthly Sales Trend",
        xaxis_title="Month",
        yaxis_title="Sales (₹)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.write(" Month-wise Growth")
    st.dataframe(
        df_trend[["month", "total_sales", "total_orders", "growth_%"]].style.format({
            "total_sales": "₹{:,.2f}",
            "growth_%":    "{:.2f}%"
        }),
        use_container_width=True
    )

except Exception as e:
    st.error(f" Sales trend error: {e}")

st.divider()

# ══════════════════════════════════════════════════
# 7. BRANCH PERFORMANCE SUMMARY
# ══════════════════════════════════════════════════
st.subheader(" Branch Performance Summary")

try:
    if is_super:
        df_perf = run_query("""
            SELECT
                b.branch_name,
                b.branch_admin_name,
                COUNT(cs.sale_id)                   AS total_orders,
                SUM(cs.gross_sales)                 AS total_sales,
                SUM(cs.received_amount)             AS received,
                SUM(cs.gross_sales - cs.received_amount) AS pending,
                ROUND(AVG(cs.gross_sales), 2)       AS avg_order_value,
                ROUND(
                    SUM(cs.received_amount) * 100.0
                    / NULLIF(SUM(cs.gross_sales), 0), 2
                ) AS collection_rate
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            GROUP BY b.branch_name, b.branch_admin_name
            ORDER BY total_sales DESC
        """)
    else:
        df_perf = run_query("""
            SELECT
                b.branch_name,
                b.branch_admin_name,
                COUNT(cs.sale_id)                   AS total_orders,
                SUM(cs.gross_sales)                 AS total_sales,
                SUM(cs.received_amount)             AS received,
                SUM(cs.gross_sales - cs.received_amount) AS pending,
                ROUND(AVG(cs.gross_sales), 2)       AS avg_order_value,
                ROUND(
                    SUM(cs.received_amount) * 100.0
                    / NULLIF(SUM(cs.gross_sales), 0), 2
                ) AS collection_rate
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            WHERE cs.branch_id = %s
            GROUP BY b.branch_name, b.branch_admin_name
            ORDER BY total_sales DESC
        """, [branch_id])

    if not df_perf.empty:
        top = df_perf.iloc[0]["branch_name"]
        top_admin = df_perf.iloc[0]["branch_admin_name"]
        st.success(f" Top Performing Branch: **{top}** — Admin: {top_admin}")

    fig = px.bar(
        df_perf, x="branch_name", y=["received", "pending"],
        barmode="stack", title="Received vs Pending per Branch",
        color_discrete_map={"received": "#2ecc71", "pending": "#e74c3c"}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df_perf.style.format({
            "total_sales":     "₹{:,.2f}",
            "received":        "₹{:,.2f}",
            "pending":         "₹{:,.2f}",
            "avg_order_value": "₹{:,.2f}",
            "collection_rate": "{:.2f}%"
        }),
        use_container_width=True
    )

except Exception as e:
    st.error(f" Branch performance error: {e}")