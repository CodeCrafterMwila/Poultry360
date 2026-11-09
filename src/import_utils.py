import openpyxl
import pandas as pd
from datetime import datetime
from src.database import get_connection

def parse_and_import_excel(file_path):
    wb = openpyxl.load_workbook(file_path, data_only=True)
    conn = get_connection()
    cursor = conn.cursor()
    
    summary_messages = []

    # --- 1. PROCESS SHEET 1 (Conventional Broiler Tracking) ---
    if 'Sheet1' in wb.sheetnames:
        sheet1 = wb['Sheet1']
        batch_name = "Conventional Batch #1 (June 2026)"
        
        # Check if batch already exists
        cursor.execute("SELECT id FROM batches WHERE batch_name = ?", (batch_name,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute("""
                INSERT INTO batches (batch_name, production_type, initial_population, placement_date, breed, supplier, expected_harvest_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (batch_name, 'Conventional', 115, '2026-06-29', 'Cobb 500', 'Local Hatchery', '2026-08-24', 'Active'))
            batch_id = cursor.lastrowid
            summary_messages.append(f"Created Conventional Batch: {batch_name} (Initial Pop: 115)")
        else:
            batch_id = row['id']
            summary_messages.append(f"Conventional Batch already exists (ID: {batch_id})")

        # Parse rows starting from row 11
        imported_days = 0
        for r in range(11, sheet1.max_row + 1):
            date_val = sheet1.cell(row=r, column=1).value
            if not date_val or not isinstance(date_val, (datetime, pd.Timestamp)):
                continue
            
            record_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
            day_str = str(sheet1.cell(row=r, column=2).value or '')
            week_str = str(sheet1.cell(row=r, column=3).value or '')
            vitamin = sheet1.cell(row=r, column=4).value
            vaccine = sheet1.cell(row=r, column=5).value
            v_status = sheet1.cell(row=r, column=6).value
            notes = sheet1.cell(row=r, column=7).value
            chickens = sheet1.cell(row=r, column=8).value
            deaths_raw = sheet1.cell(row=r, column=9).value

            day_num = int(''.join(filter(str.isdigit, day_str))) if any(char.isdigit() for char in day_str) else None
            week_num = int(''.join(filter(str.isdigit, week_str))) if any(char.isdigit() for char in week_str) else None
            
            deaths = abs(int(deaths_raw)) if deaths_raw is not None and str(deaths_raw).strip() != '' else 0
            closing_pop = int(chickens) if chickens is not None and str(chickens).strip() != '' else None

            # Insert daily record
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO daily_records (batch_id, record_date, day_number, week_number, closing_population, deaths, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (batch_id, record_date, day_num, week_num, closing_pop, deaths, notes))
                imported_days += 1
            except Exception as e:
                pass

            # Insert health record if vitamin or vaccine exists
            if vitamin or vaccine:
                item = vaccine if vaccine else vitamin
                t_type = 'Vaccine' if vaccine else 'Vitamin'
                status_mapped = 'Done' if str(v_status).strip().lower() in ['done', 'completed'] else ('Skipped' if str(v_status).strip().lower() in ['skip', 'skipped'] else 'Pending')
                
                cursor.execute("""
                    INSERT INTO health_records (batch_id, record_date, treatment_type, item_name, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (batch_id, record_date, t_type, str(item), status_mapped, str(notes) if notes else None))

        summary_messages.append(f"Imported {imported_days} daily records for Conventional Batch.")

    # --- 2. PROCESS SHEET 2 (Organic Broiler Tracking) ---
    if 'Sheet2' in wb.sheetnames:
        sheet2 = wb['Sheet2']
        org_batch_name = "Organic Batch #1 (Sept 2026)"
        
        cursor.execute("SELECT id FROM batches WHERE batch_name = ?", (org_batch_name,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute("""
                INSERT INTO batches (batch_name, production_type, initial_population, placement_date, breed, supplier, expected_harvest_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (org_batch_name, 'Organic', 107, '2026-09-04', 'Hubbard', 'Organic Hatchery', '2026-11-01', 'Active'))
            org_batch_id = cursor.lastrowid
            summary_messages.append(f"Created Organic Batch: {org_batch_name} (Initial Pop: 107)")
        else:
            org_batch_id = row['id']
            summary_messages.append(f"Organic Batch already exists (ID: {org_batch_id})")

        org_imported_days = 0
        for r in range(3, sheet2.max_row + 1):
            date_val = sheet2.cell(row=r, column=1).value
            if not date_val or not isinstance(date_val, (datetime, pd.Timestamp)):
                continue
            
            record_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
            day_str = str(sheet2.cell(row=r, column=2).value or '')
            week_str = str(sheet2.cell(row=r, column=3).value or '')
            vitamin = sheet2.cell(row=r, column=4).value
            vaccine = sheet2.cell(row=r, column=5).value
            v_status = sheet2.cell(row=r, column=6).value
            notes = sheet2.cell(row=r, column=7).value
            chickens = sheet2.cell(row=r, column=8).value
            deaths_raw = sheet2.cell(row=r, column=9).value

            day_num = int(''.join(filter(str.isdigit, day_str))) if any(char.isdigit() for char in day_str) else None
            week_num = int(''.join(filter(str.isdigit, week_str))) if any(char.isdigit() for char in week_str) else None
            
            deaths = int(deaths_raw) if deaths_raw is not None and str(deaths_raw).strip() != '' else 0
            closing_pop = int(chickens) if chickens is not None and str(chickens).strip() != '' else None

            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO daily_records (batch_id, record_date, day_number, week_number, closing_population, deaths, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (org_batch_id, record_date, day_num, week_num, closing_pop, deaths, notes))
                org_imported_days += 1
            except Exception:
                pass

            if vitamin or vaccine:
                item = vaccine if vaccine else vitamin
                t_type = 'Vaccine' if vaccine else 'Vitamin'
                status_mapped = 'Done' if str(v_status).strip().lower() in ['done', 'completed'] else ('Skipped' if str(v_status).strip().lower() in ['skip', 'skipped'] else 'Pending')
                
                cursor.execute("""
                    INSERT INTO health_records (batch_id, record_date, treatment_type, item_name, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (org_batch_id, record_date, t_type, str(item), status_mapped, str(notes) if notes else None))

        summary_messages.append(f"Imported {org_imported_days} daily records for Organic Batch.")

    conn.commit()
    conn.close()
    return summary_messages