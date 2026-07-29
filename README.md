# ECW Automation

Automates report downloads from ECW, processes the exported `.xlsx` by filtering rows per provider name, strips time from date columns, excludes completed actions, and emails the resulting files — all in one pipeline.

---

## Files

| File | Purpose |
|---|---|
| `ecw_automation.py` | Selenium browser automation class |
| `process_excel.py` | Reads downloaded `.xlsx`, filters/saves per-name reports |
| `email_sender.py` | Sends filtered reports via SMTP with SSL |
| `main.py` | Entry point — wires login → download → process → email |
| `.env` | Configuration (credentials, SMTP, email map) |

---

## Setup

### 1. Install dependencies

```bash
pip install selenium pandas openpyxl python-dotenv
```

### 2. Configure `.env`

```ini
ECW_URL=https://your-ecw-instance.com/...
ECW_USERNAME=your_username
ECW_PASSWORD=your_password

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
EMAIL_MAP={"Dimachkie":"dimachkie@example.com","Enakuaa":"enakuaa@example.com","Patel, Gunjan Silky":"gunjan@example.com"}
```

- `EMAIL_MAP` is a JSON object mapping each provider name to their email.
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833).

### 3. Update provider names

Edit `NAMES` in `main.py` to match the names you want to filter by:

```python
NAMES = ['Dimachkie', 'Enakuaa', 'Patel, Gunjan Silky']
```

---

## `ecw_automation.py` — Browser Automation

### `ECWAutomation` class

| Method | Description |
|---|---|
| `__init__()` | Initialises driver, typer, stop event, download monitor; sets `download_dir` to `~/Downloads` |
| `start()` | Launches Chrome with the configured profile, navigates to `ECW_URL` |
| `close()` | Stops download monitor, quits the browser |
| `stop()` | Signals the stop event (used to gracefully break retry loops) |
| `open(url)` | Navigates to a URL |
| `waiter(xpath, timeout)` | Waits for an element by XPath, returns it once visible. Retries every 0.5s |
| `sender(xpath, text, timeout)` | Scrolls to an element, types text with realistic human delays |
| `clicker(xpath, timeout)` | Scrolls to an element, clicks it |
| `checker(xpath, timeout=5)` | Returns `True`/`False` if an element exists and is displayed |
| `clean(xpath, timeout)` | Clicks an element, selects all text with Ctrl+A, deletes it |
| `hotkey(keys)` | Presses multiple keys simultaneously (e.g. `['control', 's']`) |
| `key(key)` | Presses a single key (e.g. `'tab'`, `'enter'`) |
| `table_clicker(table_xpath, cell_xpath, match_text, timeout, row_cell, row_text)` | Finds a row in a table by cell text and clicks it |
| `fill_icd(codes, xpath)` | Types a list of ICD codes into a field, tabbing after each |
| `switch_to_iframe(xpath, timeout)` | Finds an iframe by XPath (retry loop) and switches focus into it |
| `switch_to_default()` | Switches focus back to the top-level HTML document |
| `switch_to_parent()` | Switches focus one level up in nested iframes |
| `start_download_monitor(interval=0.5, on_complete=None)` | Starts a background thread that polls `~/Downloads`. When a new non-`.crdownload` file appears, prints its name and calls `on_complete(filepath)` |
| `stop_download_monitor()` | Stops the background polling thread |

---

## `process_excel.py` — Excel Processing

| Function | Description |
|---|---|
| `find_latest_download(download_dir)` | Returns the path of the most recently modified `.xlsx` in `~/Downloads` |
| `export_filtered_excel(names, source_path)` | Reads the `.xlsx`, finds the sheet with a `Notes` column, filters rows for each name (case-insensitive), excludes rows where `Action Status` contains "Completed", drops the first 4 columns, strips time from date columns, saves each as `{name}.xlsx` in the current directory, then auto-calls `send_emails()` |

### Filtering logic

1. Rows where the **Notes** column contains the name (case-insensitive)
2. Rows where **Action Status** does **not** contain "Completed" (case-insensitive)
3. First 4 columns are dropped
4. Date columns (`Action Created Date`, `Start Date`, `Action Due Date`, `Action Completed Date`, `Last Done Date`, `Last Due Date`) are converted to date-only format (time portion stripped)

---

## `email_sender.py` — Email Sending

| Function | Description |
|---|---|
| `send_emails(file_map)` | Reads `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, and `EMAIL_MAP` from `.env`. For each entry in `file_map`, attaches the `.xlsx` file and sends it to the corresponding email via SMTP with SSL |

---

## Pipeline Flow

```
main.py
  │
  ├── ECWAutomation.start()
  │     └── Launches Chrome → logs in → navigates to report
  │
  ├── ECWAutomation.start_download_monitor(on_complete=...)
  │     └── Background thread polls ~/Downloads every 0.5s
  │
  ├── User actions trigger report download in the browser
  │     └── File lands in ~/Downloads
  │
  ├── on_complete fires with the file path
  │     └── export_filtered_excel(NAMES, source_path=filepath)
  │           ├── Reads .xlsx
  │           ├── For each name:
  │           │     ├── Filter rows by Notes (case-insensitive)
  │           │     ├── Exclude "Completed" rows
  │           │     ├── Drop first 4 columns
  │           │     ├── Strip time from date columns
  │           │     └── Save as {name}.xlsx
  │           └── Calls send_emails(file_map)
  │                 ├── Reads EMAIL_MAP from .env
  │                 └── Sends each .xlsx to the matching email via SSL
  │
  └── ECWAutomation.close()
        └── Stops monitor, quits browser
```

---

## Running

```bash
python main.py
```

The script will open Chrome, log in, wait for you to trigger the report download, and automatically process and email the results.
