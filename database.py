"""
Database layer using Google Sheets via gspread.
Sheets:
  - รายการสินค้า: items master data
  - RP-PO: transactions (รับเข้า / จ่ายออก)

Uses st.cache_data to minimize Google Sheets API calls (limit: 300/min).
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import time

# ─── Constants ───────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ITEMS_SHEET = "สำเนาของ รายการสินค้า 1"
TX_SHEET = "สำเนาของ RP-PO"

ITEMS_HEADERS = [
    "รหัส", "รายการวัตถุดิบ", "หมวดหมู่", "หน่วยนับ",
    "ราคา/หน่วย", "สต็อกขั้นต่ำ", "คงเหลือจริง",
    "สถานะการสั่ง", "มูลค่าคงเหลือ", "อายุการเก็บ (วัน)",
]

TX_HEADERS = [
    "Approve", "Order", "วันที่", "รหัส", "รายการ",
    "ประเภท", "จำนวน", "อายุ", "life", "เวลาเหลือ", "requestner",
]

CACHE_TTL = 60  # seconds — cache reads for 60 seconds


# ─── Connection ──────────────────────────────────────────────────────────────


@st.cache_resource(ttl=600)
def get_gspread_client():
    """Create and cache a gspread client using Streamlit secrets."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(ttl=600)
def _get_spreadsheet_cached():
    """Cache the spreadsheet object to avoid repeated open_by_url calls."""
    client = get_gspread_client()
    url = st.secrets["google_sheets"]["spreadsheet_url"]
    return client.open_by_url(url)


def get_spreadsheet():
    """Get the spreadsheet object (cached)."""
    return _get_spreadsheet_cached()


def get_items_sheet():
    """Get the items worksheet."""
    return get_spreadsheet().worksheet(ITEMS_SHEET)


def get_tx_sheet():
    """Get the transactions worksheet."""
    return get_spreadsheet().worksheet(TX_SHEET)


# ─── Cache Management ───────────────────────────────────────────────────────


def clear_items_cache():
    """Clear the items data cache after a write operation."""
    _fetch_items_data.clear()
    _fetch_restock_data.clear()


def clear_tx_cache():
    """Clear the transactions data cache after a write operation."""
    _fetch_tx_data.clear()


def clear_all_cache():
    """Clear all data caches."""
    clear_items_cache()
    clear_tx_cache()


# ─── Init (ensure headers) ──────────────────────────────────────────────────


def init_db():
    """Ensure sheets exist with proper headers. Called once on app start."""
    if "db_initialized" in st.session_state:
        return  # Already initialized this session
    try:
        sp = get_spreadsheet()

        # Items sheet
        try:
            ws = sp.worksheet(ITEMS_SHEET)
            if not ws.row_values(1):
                ws.update("A1", [ITEMS_HEADERS])
        except gspread.exceptions.WorksheetNotFound:
            ws = sp.add_worksheet(title=ITEMS_SHEET, rows=100, cols=len(ITEMS_HEADERS))
            ws.update("A1", [ITEMS_HEADERS])

        # Transactions sheet
        try:
            ws = sp.worksheet(TX_SHEET)
            if not ws.row_values(1):
                ws.update("A1", [TX_HEADERS])
        except gspread.exceptions.WorksheetNotFound:
            ws = sp.add_worksheet(title=TX_SHEET, rows=1000, cols=len(TX_HEADERS))
            ws.update("A1", [TX_HEADERS])

        st.session_state["db_initialized"] = True

    except Exception as e:
        st.error(f"❌ ไม่สามารถเชื่อมต่อ Google Sheets ได้: {e}")


# ─── Helper: parse numbers safely ───────────────────────────────────────────


def _safe_float(val, default=0.0):
    """Convert value to float safely."""
    if val is None or str(val).strip() == "" or str(val).strip() == "#N/A":
        return default
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    """Convert value to int safely."""
    return int(_safe_float(val, default))


# ─── Retry wrapper ───────────────────────────────────────────────────────────


def _retry_api_call(func, max_retries=3, delay=2):
    """Retry an API call with exponential backoff on 429 errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                time.sleep(wait_time)
            else:
                raise
    return None


# ─── Cached Data Fetchers (1 API call each, cached for CACHE_TTL) ───────────


@st.cache_data(ttl=CACHE_TTL)
def _fetch_items_data() -> list[dict]:
    """Fetch all items from Google Sheets — CACHED."""
    ws = get_items_sheet()
    records = _retry_api_call(lambda: ws.get_all_records())
    items = []
    for i, row in enumerate(records):
        name = str(row.get("รายการวัตถุดิบ", "")).strip()
        if not name:
            continue
        items.append({
            "row_num": i + 2,
            "รหัส": str(row.get("รหัส", "")).strip(),
            "รายการวัตถุดิบ": name,
            "หมวดหมู่": str(row.get("หมวดหมู่", "")).strip(),
            "หน่วยนับ": str(row.get("หน่วยนับ", "")).strip(),
            "ราคา/หน่วย": _safe_float(row.get("ราคา/หน่วย")),
            "สต็อกขั้นต่ำ": _safe_float(row.get("สต็อกขั้นต่ำ")),
            "คงเหลือจริง": _safe_float(row.get("คงเหลือจริง")),
            "สถานะการสั่ง": str(row.get("สถานะการสั่ง", "")).strip(),
            "มูลค่าคงเหลือ": _safe_float(row.get("มูลค่าคงเหลือ")),
            "อายุการเก็บ (วัน)": _safe_int(row.get("อายุการเก็บ (วัน)", 0)),
        })
    return items


@st.cache_data(ttl=CACHE_TTL)
def _fetch_tx_data() -> list[dict]:
    """
    Fetch all transactions from Google Sheets — CACHED.
    Uses get_all_values() + column-index mapping instead of get_all_records()
    to avoid header-name mismatch issues.
    """
    ws = get_tx_sheet()
    all_rows = _retry_api_call(lambda: ws.get_all_values())
    if not all_rows or len(all_rows) < 2:
        return []

    # Column index mapping (0-based):
    # A=0:Approve, B=1:Order, C=2:วันที่, D=3:รหัส, E=4:รายการ,
    # F=5:ประเภท, G=6:จำนวน, H=7:อายุ, I=8:life, J=9:เวลาเหลือ, K=10:requestner
    txs = []
    for i, row in enumerate(all_rows[1:]):  # skip header
        # Pad row to 11 columns if shorter
        while len(row) < 11:
            row.append("")

        item_code = str(row[3]).strip()
        item_name = str(row[4]).strip()
        order_val = str(row[1]).strip()

        # Skip empty rows
        if not order_val and not item_code:
            continue
        # Skip example rows
        if item_name == "ตัวอย่าง":
            continue

        txs.append({
            "row_num": i + 2,
            "Approve": str(row[0]).strip().upper(),
            "Order": order_val,
            "วันที่": str(row[2]).strip(),
            "รหัส": item_code,
            "รายการ": item_name,
            "ประเภท": str(row[5]).strip(),
            "จำนวน": _safe_float(row[6]),
            "อายุ": _safe_int(row[7]),
            "life": str(row[8]).strip(),
            "เวลาเหลือ": _safe_int(row[9]),
            "requestner": str(row[10]).strip(),
        })
    return txs


@st.cache_data(ttl=CACHE_TTL)
def _fetch_restock_data() -> list[dict]:
    """Fetch restock report — CACHED (reuses items cache internally)."""
    items = _fetch_items_data()
    return [
        {
            **item,
            "need_to_restock": item["สต็อกขั้นต่ำ"] - item["คงเหลือจริง"],
        }
        for item in items
        if item["คงเหลือจริง"] < item["สต็อกขั้นต่ำ"]
    ]


# ─── Public Read Functions (use cache) ──────────────────────────────────────


def get_all_items() -> list[dict]:
    """Return all items (cached)."""
    return _fetch_items_data()


def get_item_by_code(code: str) -> dict | None:
    """Find an item by its code (uses cache)."""
    for item in get_all_items():
        if item["รหัส"] == code:
            return item
    return None


def get_all_transactions() -> list[dict]:
    """Return all transactions (cached)."""
    return _fetch_tx_data()


def get_transactions(date_filter: date | None = None, tx_type: str | None = None,
                     item_code: str | None = None) -> list[dict]:
    """Get transactions with optional filters (uses cache)."""
    txs = get_all_transactions()

    if date_filter:
        date_str = date_filter.strftime("%d/%m/%y")
        txs = [t for t in txs if t["วันที่"] == date_str]

    if tx_type:
        txs = [t for t in txs if t["ประเภท"] == tx_type]

    if item_code:
        txs = [t for t in txs if t["รหัส"] == item_code]

    return txs


def get_today_transaction_count() -> int:
    """Count today's transactions (uses cache)."""
    today_str = date.today().strftime("%d/%m/%y")
    txs = get_all_transactions()
    return sum(1 for t in txs if t["วันที่"] == today_str)


def get_restock_report() -> list[dict]:
    """Return items below minimum stock (cached)."""
    return _fetch_restock_data()


# ─── Category → Prefix mapping ──────────────────────────────────────────────

CATEGORY_PREFIX = {
    "เนื้อสัตว์": "MT",
    "อาหารทะเล": "SP",
    "อาหารสำเร็จ": "SF",
    "ไข่/นม": "VG",
    "ของแห้ง": "DG",
}


def _generate_item_code(category: str) -> str:
    """
    Generate a unique item code for a category.
    Scans BOTH current items AND all RP-PO history to find the highest
    number ever used, then increments. This ensures codes are never reused.
    """
    prefix = CATEGORY_PREFIX.get(category, "OT")
    max_num = 0

    # Scan current items
    items = get_all_items()
    for item in items:
        code = item["รหัส"]
        if code.startswith(prefix + "-"):
            try:
                num = int(code.split("-")[1])
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                pass

    # Scan RP-PO history for codes that may have been deleted
    txs = get_all_transactions()
    for tx in txs:
        code = tx["รหัส"]
        if code.startswith(prefix + "-"):
            try:
                num = int(code.split("-")[1])
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                pass

    return f"{prefix}-{max_num + 1:04d}"


# ─── Write Functions (clear cache after write) ──────────────────────────────


def add_item(name: str, category: str, unit: str,
             price: float, min_qty: float, current_qty: float, shelf_life: int):
    """
    Add a new item with auto-generated code.
    Code is generated in Python (not ARRAYFORMULA) to prevent reuse after deletion.
    """
    code = _generate_item_code(category)
    ws = get_items_sheet()
    status = "ต้องสั่ง" if current_qty < min_qty else "ปกติ"
    value = current_qty * price

    col_b = _retry_api_call(lambda: ws.col_values(2))
    next_row = len(col_b) + 1

    # Write A:J (code is now Python-generated, not ARRAYFORMULA)
    _retry_api_call(lambda: ws.update(
        f"A{next_row}:J{next_row}",
        [[code, name, category, unit, price, min_qty, current_qty, status, value, shelf_life]],
        value_input_option="USER_ENTERED",
    ))

    clear_items_cache()
    return code


def update_item(row_num: int, name: str, category: str,
                unit: str, price: float, min_qty: float, shelf_life: int):
    """Update an item — clears items cache after."""
    ws = get_items_sheet()
    _retry_api_call(lambda: ws.update(f"B{row_num}:F{row_num}", [[name, category, unit, price, min_qty]]))
    _retry_api_call(lambda: ws.update(f"J{row_num}", [[shelf_life]]))
    clear_items_cache()


def delete_item(row_num: int):
    """Delete an item — clears items cache after."""
    ws = get_items_sheet()
    _retry_api_call(lambda: ws.delete_rows(row_num))
    clear_items_cache()


def recalculate_item_stock(item_code: str):
    """Recalculate stock for an item from transactions and update sheet."""
    # Force fresh data for recalculation
    clear_all_cache()
    items = get_all_items()
    item = None
    for it in items:
        if it["รหัส"] == item_code:
            item = it
            break
    if not item:
        return

    txs = get_all_transactions()
    total_in = sum(t["จำนวน"] for t in txs if t["รหัส"] == item_code and t["ประเภท"] == "รับเข้า" and t["Approve"] == "TRUE")
    total_out = sum(t["จำนวน"] for t in txs if t["รหัส"] == item_code and t["ประเภท"] == "จ่ายออก" and t["Approve"] == "TRUE")

    current_qty = total_in - total_out
    price = item["ราคา/หน่วย"]
    min_qty = item["สต็อกขั้นต่ำ"]
    status = "ต้องสั่ง" if current_qty < min_qty else "ปกติ"
    value = current_qty * price

    ws = get_items_sheet()
    row_num = item["row_num"]
    _retry_api_call(lambda: ws.update(
        f"G{row_num}:I{row_num}",
        [[current_qty, status, value]],
        value_input_option="USER_ENTERED",
    ))

    clear_items_cache()


def add_transaction(item_code: str, item_name: str, tx_type: str,
                    quantity: float, shelf_life: int, requester: str,
                    approve: bool = True):
    """Add a transaction — uses batch_update for atomic write."""
    ws = get_tx_sheet()

    today = date.today()
    today_str = today.strftime("%d/%m/%y")
    life_date = today + timedelta(days=shelf_life)
    life_str = life_date.strftime("%d/%m/%y")
    remaining_days = shelf_life

    # Find next empty row
    all_vals = _retry_api_call(lambda: ws.get_all_values())
    next_row = len(all_vals) + 1 if all_vals else 2

    # Batch write: A (Approve) + C:K (data) in ONE API call
    _retry_api_call(lambda: ws.batch_update([
        {
            "range": f"A{next_row}",
            "values": [[str(approve).upper()]],
        },
        {
            "range": f"C{next_row}:K{next_row}",
            "values": [[today_str, item_code, item_name, tx_type,
                        quantity, shelf_life, life_str, remaining_days, requester]],
        },
    ], value_input_option="USER_ENTERED"))

    clear_all_cache()

    # Recalculate stock
    recalculate_item_stock(item_code)

    # Read back order number
    order_num = _retry_api_call(lambda: ws.cell(next_row, 2).value) or f"ROW-{next_row}"
    return str(order_num)


def approve_transaction(row_num: int):
    """Set Approve to TRUE for a transaction row."""
    ws = get_tx_sheet()
    _retry_api_call(lambda: ws.update(f"A{row_num}", [["TRUE"]], value_input_option="USER_ENTERED"))
    item_code = _retry_api_call(lambda: ws.cell(row_num, 4).value)
    if item_code:
        recalculate_item_stock(item_code.strip())
    clear_all_cache()
