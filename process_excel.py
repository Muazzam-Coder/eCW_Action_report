import os
import re
import pandas as pd

from email_sender import send_emails

DATE_COLS = [
    "Action Created Date", "Start Date", "Action Due Date",
    "Action Completed Date", "Last Done Date", "Last Due Date",
]


def _strip_time(val):
    if pd.isna(val):
        return val
    s = str(val).strip()
    return re.sub(r'\s+\d{1,2}:\d{2}(:\d{2})?(\s*[APap][Mm])?$', '', s)


def find_latest_download(download_dir=None):
    if download_dir is None:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    xlsx_files = [
        os.path.join(download_dir, f)
        for f in os.listdir(download_dir)
        if f.endswith(".xlsx") and not f.startswith("~$")
    ]
    if not xlsx_files:
        raise FileNotFoundError(f"No .xlsx files found in {download_dir}")
    return max(xlsx_files, key=os.path.getmtime)


def export_filtered_excel(names, source_path=None):
    if source_path is None:
        source_path = find_latest_download()

    xls = pd.ExcelFile(source_path)
    sheet = None
    df = None
    for s in xls.sheet_names:
        temp = xls.parse(s, dtype=str)
        temp.columns = temp.columns.str.strip()
        if "Notes" in temp.columns:
            sheet = s
            df = temp
            break
    if df is None:
        raise ValueError(f"No sheet with 'Notes' column found in {source_path}")

    file_map = {}
    for name in names:
        mask = df["Notes"].str.contains(name, case=False, na=False)
        if "Action Status" in df.columns:
            mask = mask & ~df["Action Status"].str.contains("Completed", case=False, na=False)
        filtered = df.loc[mask, df.columns[4:]].copy()
        if filtered.empty:
            print(f"    No rows for '{name}'")
            continue
        for col in DATE_COLS:
            if col in filtered.columns:
                filtered[col] = filtered[col].apply(_strip_time)
        out_path = os.path.join(os.getcwd(), f"{name}.xlsx")
        filtered.to_excel(out_path, index=False)
        print(f"    Exported {out_path} ({len(filtered)} rows)")
        file_map[name] = out_path

    if file_map:
        send_emails(file_map)
        for name, path in file_map.items():
            if os.path.isfile(path):
                os.remove(path)
                print(f"    Deleted {name}.xlsx")

    return file_map
