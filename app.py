import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Poultry360 - Smart Broiler Management",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE CONNECTION HELper (WITH TIMEOUT) ---
DB_NAME = "poultry360.db"

def get_connection():
    # timeout=10.0 prevents "database is locked" errors by waiting for active writes to clear
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

# --- INITIALIZE CORE TABLES ---
def init_db():
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_name TEXT UNIQUE,
                production_type TEXT,
                initial_population INTEGER,
                placement_date TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://img.icons8.com/color/96/chicken.png", width=64)
st.sidebar.title("Poultry360")

# --- DEVELOPER BRANDING TAG ---
st.sidebar.markdown(
    """
    <div style='background-color: #1e293b; padding: 10px; border-radius: 8px; border: 1px solid #334155; margin-top: 10px; margin-bottom: 10px;'>
        <p style='color: #94a3b8; font-size: 11px; margin: 0;'>DEVELOPER</p>
        <p style='color: #f8fafc; font-size: 13px; font-weight: bold; margin: 0;'>Mwila Singoma</p>
        <p style='color: #38bdf8; font-size: 11px; margin: 0;'>AKA CodeCrafterMwila</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Workbook Import", "Flock Management", "Daily Records", "Health & Vaccines", "Financials", "Analytics"]
)

st.sidebar.markdown("---")
st.sidebar.info("Tailored for Zambian Agri-Operations 🇿🇲")

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "Dashboard":
    st.title("📊 Farm Performance Dashboard")
    st.markdown("Overview of active broiler batches, mortality rates, and operational status.")
    
    conn = get_connection()
    try:
        df_batches = pd.read_sql_query("SELECT * FROM batches", conn)
    except Exception:
        df_batches = pd.DataFrame()
    finally:
        conn.close()
        
    if not df_batches.empty:
        total_batches = len(df_batches)
        total_initial_birds = df_batches['initial_population'].sum() if 'initial_population' in df_batches.columns else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Registered Batches", total_batches)
        col2.metric("Total Initial Birds", f"{total_initial_birds:,}")
        col3.metric("Operational Status", "Active 🟢")
        
        st.markdown("---")
        st.subheader("Active Batches Summary")
        st.dataframe(df_batches, use_container_width=True)
    else:
        st.info("No batches found. Go to **Flock Management** or **Workbook Import** to get started.")

# ==========================================
# 2. WORKBOOK IMPORT
# ==========================================
elif menu == "Workbook Import":
    st.title("📁 Excel Workbook Import")
    st.markdown("Upload legacy broiler tracking sheets to sync data directly into the database.")
    
    uploaded_file = st.file_uploader("Upload Excel Tracker (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df_imported = pd.read_excel(uploaded_file)
            st.success("Workbook successfully parsed!")
            st.dataframe(df_imported.head(), use_container_width=True)
            
            if st.button("Import into Database"):
                conn = get_connection()
                try:
                    df_imported.to_sql("imported_records", conn, if_exists="append", index=False)
                    conn.commit()
                    st.success("Data successfully synced to SQLite backend!")
                except Exception as e:
                    st.error(f"Import error: {e}")
                finally:
                    conn.close()
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")

# ==========================================
# 3. FLOCK MANAGEMENT
# ==========================================
elif menu == "Flock Management":
    st.title("🐔 Flock & Batch Management")
    st.markdown("Create and manage your conventional or organic broiler batches.")
    
    with st.form("new_batch_form"):
        st.subheader("Register New Batch")
        batch_name = st.text_input("Batch Name (e.g., Conventional Batch #2)")
        production_type = st.selectbox("Production Type", ["Conventional", "Organic"])
        initial_population = st.number_input("Initial Bird Population", min_value=1, value=100)
        start_date = st.date_input("Start Date")
        
        submitted = st.form_submit_button("Create Batch")
        if submitted and batch_name:
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(batches);")
                columns = [col[1] for col in cursor.fetchall()]
                
                if "placement_date" in columns:
                    conn.execute(
                        "INSERT INTO batches (batch_name, production_type, initial_population, placement_date) VALUES (?, ?, ?, ?)",
                        (batch_name, production_type, initial_population, str(start_date))
                    )
                else:
                    try:
                        conn.execute("ALTER TABLE batches ADD COLUMN start_date TEXT;")
                    except Exception:
                        pass
                    conn.execute(
                        "INSERT INTO batches (batch_name, production_type, initial_population, start_date) VALUES (?, ?, ?, ?)",
                        (batch_name, production_type, initial_population, str(start_date))
                    )
                conn.commit()
                st.success(f"Successfully created batch: {batch_name}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating batch: {e}")
            finally:
                conn.close()

    st.markdown("---")
    st.subheader("Existing Batches Overview")
    conn = get_connection()
    try:
        df_batches = pd.read_sql_query("SELECT * FROM batches", conn)
    except Exception:
        df_batches = pd.DataFrame()
    finally:
        conn.close()
    
    if not df_batches.empty:
        st.dataframe(df_batches, use_container_width=True)
    else:
        st.info("No batches registered yet.")

# ==========================================
# 4. DAILY RECORDS
# ==========================================
elif menu == "Daily Records":
    st.title("📝 Daily Operational Logs")
    st.markdown("Log daily mortality, feed intake, and weight progression.")
    
    conn = get_connection()
    try:
        batches = conn.execute("SELECT * FROM batches").fetchall()
    except Exception:
        batches = []
    finally:
        conn.close()
    
    if batches:
        batch_names = [b['batch_name'] for b in batches]
        selected_batch_name = st.selectbox("Select Batch for Logging", batch_names)
        selected_batch = next(b for b in batches if b['batch_name'] == selected_batch_name)
        
        with st.form("daily_log_form"):
            col1, col2 = st.columns(2)
            with col1:
                day_number = st.number_input("Day Number", min_value=1, value=1)
                mortality = st.number_input("Mortality (Birds Lost)", min_value=0, value=0)
            with col2:
                feed_consumed = st.number_input("Feed Consumed (Kg)", min_value=0.0, value=0.0, step=0.5)
                avg_weight = st.number_input("Average Body Weight (g)", min_value=0.0, value=0.0, step=10.0)
                
            log_submitted = st.form_submit_button("Save Daily Record")
            if log_submitted:
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA table_info(daily_records);")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    if not columns:
                        conn.execute("""
                            CREATE TABLE IF NOT EXISTS daily_records (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                batch_id INTEGER,
                                day_number INTEGER,
                                mortality INTEGER,
                                feed_consumed_kg REAL,
                                avg_weight_g REAL,
                                record_date TEXT,
                                FOREIGN KEY (batch_id) REFERENCES batches (id)
                            )
                        """)
                        conn.commit()
                        cursor.execute("PRAGMA table_info(daily_records);")
                        columns = [col[1] for col in cursor.fetchall()]
                    
                    required_cols = {
                        "day_number": "INTEGER",
                        "mortality": "INTEGER",
                        "feed_consumed_kg": "REAL",
                        "avg_weight_g": "REAL",
                        "record_date": "TEXT"
                    }
                    for col_name, col_type in required_cols.items():
                        if col_name not in columns:
                            try:
                                conn.execute(f"ALTER TABLE daily_records ADD COLUMN {col_name} {col_type};")
                                conn.commit()
                            except Exception:
                                pass
                    
                    today_str = str(date.today())
                    if "record_date" in columns:
                        try:
                            conn.execute(
                                """INSERT INTO daily_records (batch_id, day_number, mortality, feed_consumed_kg, avg_weight_g, record_date) 
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (selected_batch['id'], day_number, mortality, feed_consumed, avg_weight, today_str)
                            )
                        except Exception:
                            conn.execute(
                                """INSERT INTO daily_records (batch_id, day_number, mortality, feed_consumed_kg, avg_weight_g) 
                                   VALUES (?, ?, ?, ?, ?)""",
                                (selected_batch['id'], day_number, mortality, feed_consumed, avg_weight)
                            )
                    else:
                        conn.execute(
                            """INSERT INTO daily_records (batch_id, day_number, mortality, feed_consumed_kg, avg_weight_g) 
                               VALUES (?, ?, ?, ?, ?)""",
                            (selected_batch['id'], day_number, mortality, feed_consumed, avg_weight)
                        )
                    conn.commit()
                    st.success(f"Logged Day {day_number} records for {selected_batch_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving daily record: {e}")
                finally:
                    conn.close()
        
        st.markdown("### 📋 Logged History")
        conn = get_connection()
        try:
            df_logs = pd.read_sql_query(
                "SELECT * FROM daily_records WHERE batch_id = ?",
                conn,
                params=(selected_batch['id'],)
            )
            if not df_logs.empty:
                df_logs.columns = [str(col).strip() for col in df_logs.columns]
                st.dataframe(df_logs, use_container_width=True)
            else:
                st.info("No daily logs recorded for this batch yet.")
        except Exception as e:
            st.info(f"No daily records table initialized yet or error: {e}")
        finally:
            conn.close()
    else:
        st.warning("Please create a batch in **Flock Management** first.")

# ==========================================
# 5. HEALTH & VACCINES
# ==========================================
elif menu == "Health & Vaccines":
    st.title("💉 Health, Vitamins & Vaccination Schedule")
    st.markdown("Manage vaccination timelines, vitamin programs, and medication logs for your flocks.")
    
    conn = get_connection()
    try:
        batches = conn.execute("SELECT * FROM batches").fetchall()
    except Exception:
        batches = []
    finally:
        conn.close()
    
    if batches:
        batch_names = [b['batch_name'] for b in batches]
        selected_batch_name = st.selectbox("Select Batch", batch_names, key="health_batch_select")
        selected_batch = next(b for b in batches if b['batch_name'] == selected_batch_name)
        
        with st.form("health_log_form"):
            st.subheader("Schedule / Administer Treatment")
            col1, col2 = st.columns(2)
            with col1:
                treatment_type = st.selectbox("Type", ["Vaccine (Gumboro)", "Vaccine (Newcastle)", "Vitamins", "Antibiotic", "Anti-stress"])
                treatment_name = st.text_input("Specific Product Name (e.g., Lasota, Vita-Stress)")
                target_day = st.number_input("Target Day Number", min_value=1, value=7)
            with col2:
                administration_date = st.date_input("Date Administered / Scheduled")
                status = st.selectbox("Status", ["Scheduled", "Administered", "Completed"])
                notes = st.text_area("Dosage & Administration Notes")
                
            health_submitted = st.form_submit_button("Save Health Record")
            if health_submitted:
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("PRAGMA table_info(health_records);")
                        columns = [col[1] for col in cursor.fetchall()]
                    except Exception:
                        columns = []
                    
                    if not columns:
                        conn.execute("""
                            CREATE TABLE IF NOT EXISTS health_records (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                batch_id INTEGER,
                                treatment_type TEXT,
                                treatment_name TEXT,
                                target_day INTEGER,
                                administration_date TEXT,
                                status TEXT,
                                notes TEXT,
                                FOREIGN KEY (batch_id) REFERENCES batches (id)
                            )
                        """)
                        conn.commit()
                        cursor.execute("PRAGMA table_info(health_records);")
                        columns = [col[1] for col in cursor.fetchall()]
                    
                    required_cols = {
                        "treatment_type": "TEXT",
                        "treatment_name": "TEXT",
                        "target_day": "INTEGER",
                        "administration_date": "TEXT",
                        "status": "TEXT",
                        "notes": "TEXT"
                    }
                    for col_name, col_type in required_cols.items():
                        if col_name not in columns:
                            try:
                                conn.execute(f"ALTER TABLE health_records ADD COLUMN {col_name} {col_type};")
                                conn.commit()
                            except Exception:
                                pass
                    
                    conn.execute(
                        """INSERT INTO health_records (batch_id, treatment_type, treatment_name, target_day, administration_date, status, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (selected_batch['id'], treatment_type, treatment_name, target_day, str(administration_date), status, notes)
                    )
                    conn.commit()
                    st.success(f"Health record saved for {selected_batch_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving health record: {e}")
                finally:
                    conn.close()
                
        st.markdown("### 📋 Batch Health & Vaccination Timeline")
        conn = get_connection()
        try:
            df_health = pd.read_sql_query(
                "SELECT * FROM health_records WHERE batch_id = ?",
                conn,
                params=(selected_batch['id'],)
            )
            if not df_health.empty:
                df_health.columns = [str(col).strip() for col in df_health.columns]
                st.dataframe(df_health, use_container_width=True)
            else:
                st.info("No vaccination or health records logged for this batch yet.")
        except Exception as e:
            st.info(f"No health records table initialized yet or error: {e}")
        finally:
            conn.close()
    else:
        st.warning("Please create a batch in **Flock Management** first.")

# ==========================================
# 6. FINANCIALS
# ==========================================
elif menu == "Financials":
    st.title("💰 Financial Management & Ledger")
    st.markdown("Track feed costs, medication expenses, operational outlays, and revenue projections (ZMW).")
    
    conn = get_connection()
    try:
        batches = conn.execute("SELECT * FROM batches").fetchall()
    except Exception:
        batches = []
    finally:
        conn.close()
    
    if batches:
        batch_names = [b['batch_name'] for b in batches]
        selected_batch_name = st.selectbox("Select Batch", batch_names, key="fin_batch_select")
        selected_batch = next(b for b in batches if b['batch_name'] == selected_batch_name)
        
        with st.form("financial_form"):
            st.subheader("Add Financial Transaction")
            col1, col2 = st.columns(2)
            with col1:
                tx_type = st.selectbox("Transaction Type", ["Expense (Feed)", "Expense (Medication)", "Expense (Chicks/Stock)", "Expense (Utilities/Other)", "Revenue (Bird Sales)", "Revenue (Manure Sales)"])
                item_desc = st.text_input("Description (e.g., 50kg Starter Crumbs, 100 Broiler Chicks)")
                amount_zmw = st.number_input("Amount (ZMW)", min_value=0.0, value=0.0, step=50.0)
            with col2:
                tx_date = st.date_input("Transaction Date")
                notes = st.text_area("Remarks / Supplier Notes")
                
            fin_submitted = st.form_submit_button("Save Financial Entry")
            if fin_submitted:
                conn = get_connection()
                try:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS financial_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            batch_id INTEGER,
                            tx_type TEXT,
                            item_desc TEXT,
                            amount_zmw REAL,
                            tx_date TEXT,
                            notes TEXT,
                            FOREIGN KEY (batch_id) REFERENCES batches (id)
                        )
                    """)
                    conn.execute(
                        """INSERT INTO financial_records (batch_id, tx_type, item_desc, amount_zmw, tx_date, notes)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (selected_batch['id'], tx_type, item_desc, amount_zmw, str(tx_date), notes)
                    )
                    conn.commit()
                    st.success(f"Financial record saved for {selected_batch_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving financial entry: {e}")
                finally:
                    conn.close()
                
        st.markdown("### 📊 Financial Ledger & P&L Overview")
        conn = get_connection()
        try:
            df_fin = pd.read_sql_query(
                "SELECT tx_date, tx_type, item_desc, amount_zmw, notes FROM financial_records WHERE batch_id = ? ORDER BY tx_date",
                conn,
                params=(selected_batch['id'],)
            )
            if not df_fin.empty:
                total_expenses = df_fin[df_fin['tx_type'].str.contains("Expense")]['amount_zmw'].sum()
                total_revenue = df_fin[df_fin['tx_type'].str.contains("Revenue")]['amount_zmw'].sum()
                net_profit = total_revenue - total_expenses
                
                fcol1, fcol2, fcol3 = st.columns(3)
                fcol1.metric("Total Expenses (ZMW)", f"{total_expenses:,.2f}")
                fcol2.metric("Total Revenue (ZMW)", f"{total_revenue:,.2f}")
                fcol3.metric("Net Profit / Loss (ZMW)", f"{net_profit:,.2f}", delta=f"{net_profit:,.2f}")
                
                st.markdown("---")
                st.dataframe(df_fin, use_container_width=True)
            else:
                st.info("No financial transactions recorded for this batch yet.")
        except Exception:
            st.info("Financial records table initialized on first entry.")
        finally:
            conn.close()
    else:
        st.warning("Please create a batch in **Flock Management** first.")

# ==========================================
# 7. ANALYTICS
# ==========================================
elif menu == "Analytics":
    st.title("📈 Advanced Analytics & FCR")
    st.markdown("Analyze Feed Conversion Ratio (FCR), growth curves, and performance benchmarking.")
    
    conn = get_connection()
    try:
        batches = conn.execute("SELECT * FROM batches").fetchall()
    except Exception:
        batches = []
    finally:
        conn.close()
    
    if batches:
        batch_names = [b['batch_name'] for b in batches]
        selected_batch_name = st.selectbox("Select Batch for Analytics", batch_names, key="analytics_batch_select")
        selected_batch = next(b for b in batches if b['batch_name'] == selected_batch_name)
        
        conn = get_connection()
        try:
            df_records = pd.read_sql_query(
                "SELECT * FROM daily_records WHERE batch_id = ? ORDER BY day_number",
                conn,
                params=(selected_batch['id'],)
            )
        except Exception:
            df_records = pd.DataFrame()
        finally:
            conn.close()
        
        if not df_records.empty:
            df_records.columns = [str(col).strip().lower() for col in df_records.columns]
            
            st.subheader("📊 Performance & Growth Metrics")
            
            feed_col = next((c for c in df_records.columns if 'feed' in c), None)
            weight_col = next((c for c in df_records.columns if 'weight' in c or 'wt' in c), None)
            day_col = next((c for c in df_records.columns if 'day' in c), df_records.columns[0])
            
            col1, col2 = st.columns(2)
            
            if feed_col and weight_col:
                import plotly.express as px
                
                fig_wt = px.line(
                    df_records,
                    x=day_col,
                    y=weight_col,
                    markers=True,
                    title=f"Body Weight Progression (g) - {selected_batch_name}",
                    template="plotly_dark"
                )
                fig_wt.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                col1.plotly_chart(fig_wt, use_container_width=True)
                
                fig_feed = px.line(
                    df_records,
                    x=day_col,
                    y=feed_col,
                    markers=True,
                    title=f"Feed Intake (kg) - {selected_batch_name}",
                    template="plotly_dark"
                )
                fig_feed.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                col2.plotly_chart(fig_feed, use_container_width=True)
                
                st.markdown("---")
                st.subheader("⚡ Feed Conversion Ratio (FCR) Insights")
                total_feed = df_records[feed_col].sum()
                max_weight = df_records[weight_col].max()
                initial_pop = selected_batch['initial_population']
                
                mort_col = next((c for c in df_records.columns if 'mort' in c or 'dead' in c), None)
                total_mortality = df_records[mort_col].sum() if mort_col else 0
                current_birds = initial_pop - total_mortality
                
                if max_weight > 0 and current_birds > 0:
                    total_biomass_kg = (current_birds * max_weight) / 1000.0
                    fcr = total_feed / total_biomass_kg if total_biomass_kg > 0 else 0
                    
                    acol1, acol2, acol3 = st.columns(3)
                    acol1.metric("Total Feed Consumed", f"{total_feed:,.2f} kg")
                    acol2.metric("Estimated Total Biomass", f"{total_biomass_kg:,.2f} kg")
                    acol3.metric("Calculated FCR", f"{fcr:.2f}", help="Lower FCR indicates better feed efficiency (ideal broiler target: 1.5 - 1.8)")
                else:
                    st.info("Enter average weight and bird counts to compute live FCR.")
            else:
                st.warning("Daily records require feed and weight columns for advanced FCR analytics.")
        else:
            st.info("No daily records found for this batch.")
    else:
        st.warning("Please create a batch in **Flock Management** first.")