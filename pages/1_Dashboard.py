import streamlit as st
import pandas as pd
import psycopg2

# ── Guard: must be logged in ──────────────────────
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

# ── User info ─────────────────────────────────────
name      = st.session_state.user["username"]
branch_id = st.session_state.user["branch_id"]

TABLES = ["customer_sales", "payment_splits", "users", "branches"]

# ── Auto detect primary key ───────────────────────
def get_primary_key(table_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.key_column_usage
        WHERE table_name = %s
        AND constraint_name IN (
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_name = %s AND constraint_type = 'PRIMARY KEY'
        ) LIMIT 1
    """, (table_name, table_name))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

# ── Fetch data ────────────────────────────────────
def get_table_data(table_name, branch_id):
    conn = get_connection()
    cur = conn.cursor()
    if branch_id == 0:
        cur.execute(f"SELECT * FROM {table_name} LIMIT 1000")
    else:
        try:
            cur.execute(f"SELECT * FROM {table_name} WHERE branch_id = %s LIMIT 1000", (branch_id,))
        except:
            cur.execute(f"SELECT * FROM {table_name} LIMIT 1000")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return cols, rows

# ── Update ────────────────────────────────────────
def update_row(table_name, primary_key, pk_value, updated_data):
    conn = get_connection()
    cur = conn.cursor()
    set_clause = ", ".join([f"{col} = %s" for col in updated_data.keys()])
    values = list(updated_data.values()) + [pk_value]
    cur.execute(f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = %s", values)
    conn.commit()
    cur.close()
    conn.close()

# ── Add ───────────────────────────────────────────
def add_row(table_name, new_data):
    conn = get_connection()
    cur = conn.cursor()
    cols = ", ".join(new_data.keys())
    placeholders = ", ".join(["%s"] * len(new_data))
    cur.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", list(new_data.values()))
    conn.commit()
    cur.close()
    conn.close()

# ── Delete ────────────────────────────────────────
def delete_row(table_name, primary_key, pk_value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table_name} WHERE {primary_key} = %s", (pk_value,))
    conn.commit()
    cur.close()
    conn.close()

# ── Page ──────────────────────────────────────────
if name == "superadmin":
    st.title(" Dashboard — Super Admin")
    st.info("You can view and edit all branches")
else:
    st.title(f" Dashboard — {name}")
    st.info(f" Viewing Branch ID: {branch_id}")

st.divider()

selected_table = st.selectbox(" Select Table", TABLES)
pk = get_primary_key(selected_table)

if not pk:
    st.error(f"Could not find primary key for {selected_table}")
else:
    cols, rows = get_table_data(selected_table, branch_id)
    df = pd.DataFrame(rows, columns=cols)

    st.subheader(f" {selected_table.upper()}")
    st.dataframe(df, use_container_width=True)
    st.divider()

    # ── Edit ──────────────────────────────────────
    st.subheader(" Add sales entry")
    pk_values = df[pk].tolist()
    selected_pk = st.selectbox(f"Select {pk} to edit", pk_values)

    if selected_pk:
        row_to_edit = df[df[pk] == selected_pk].iloc[0]
        updated_data = {}
        with st.form("edit_form"):
            for col in cols:
                if col == pk:
                    continue
                if col == "branch_id" and branch_id != 0:
                    st.text_input(col, value=str(row_to_edit[col]), disabled=True)
                    updated_data[col] = row_to_edit[col]
                else:
                    updated_data[col] = st.text_input(col, value=str(row_to_edit[col]))
            if st.form_submit_button(" Save Changes"):
                try:
                    update_row(selected_table, pk, selected_pk, updated_data)
                    st.success(" Row updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f" {e}")

    st.divider()

    # ── Add ───────────────────────────────────────
    st.subheader(" Add New sales")
    new_data = {}
    with st.form("add_form"):
        for col in cols:
            if col == pk:
                continue
            if col == "branch_id" and branch_id != 0:
                st.text_input(col, value=str(branch_id), disabled=True)
                new_data[col] = branch_id
            else:
                new_data[col] = st.text_input(col)
        if st.form_submit_button(" Add Row"):
            try:
                add_row(selected_table, new_data)
                st.success(" Row added!")
                st.rerun()
            except Exception as e:
                st.error(f" {e}")

    st.divider()

    # ── Delete ────────────────────────────────────
    st.subheader("Delete entry")
    delete_pk = st.selectbox(f"Select {pk} to delete", pk_values, key="delete")

    if branch_id != 0:
        row_branch = df[df[pk] == delete_pk]["branch_id"].values
        if len(row_branch) > 0 and row_branch[0] != branch_id:
            st.error(" You can only delete rows from your own branch")
            delete_pk = None

    if delete_pk and st.button(" Delete Row"):
        try:
            delete_row(selected_table, pk, delete_pk)
            st.success(" Row deleted!")
            st.rerun()
        except Exception as e:
            st.error(f" {e}")