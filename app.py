import streamlit as st
import pandas as pd
from datetime import date, datetime
import database as db

# ─── Initialize ──────────────────────────────────────────────────────────────

db.init_db()

st.set_page_config(
    page_title="📦 Sukiism Stock",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Noto Sans Thai', sans-serif; }

    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1200px;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea0d, #764ba20d);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.85rem !important;
        color: #64748b !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }

    .status-ok {
        background: #dcfce7; color: #166534;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: 600;
        display: inline-block;
    }
    .status-low {
        background: #fee2e2; color: #991b1b;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: 600;
        display: inline-block;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b, #0f172a);
    }
    [data-testid="stSidebar"] .stRadio label { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        color: #cbd5e1 !important;
        font-size: 1rem !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
        background: #334155 !important;
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span { color: #e2e8f0 !important; }

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: none;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .stAlert { border-radius: 10px !important; }

    .page-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .page-subheader {
        color: #64748b; font-size: 1rem; margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ─── Category Options ────────────────────────────────────────────────────────

CATEGORIES = ["เนื้อสัตว์", "อาหารทะเล","อาหารสำเร็จ", "ไข่/นม", "ของแห้ง"]

# ─── Sidebar Navigation ─────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📦 Sukiism")
    st.markdown("---")

    page = st.radio(
        "เมนู",
        ["📊 Dashboard", "📦 จัดการ Stock", "➕ รับเข้า", "🔻 จ่ายออก", "📋 Transactions"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if st.button("🔄 Refresh ข้อมูล", use_container_width=True):
        db.clear_all_cache()
        st.rerun()
    st.markdown(
        "<p style='font-size:0.7rem;color:#64748b;text-align:center;'>"
        "ข้อมูล cache อัตโนมัติ 60 วินาที<br>กด Refresh เพื่ออัพเดทล่าสุด</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        f"<p style='font-size:0.75rem;color:#94a3b8;text-align:center;'>"
        f"📅 {db.thai_today().strftime('%d/%m/%Y')}<br>Sukiism Stock v2.0</p>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 1 : DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

if page == "📊 Dashboard":
    st.markdown('<p class="page-header">📊 Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subheader">ภาพรวมสต็อกวัตถุดิบ Sukiism</p>', unsafe_allow_html=True)

    items = db.get_all_items()
    restock = db.get_restock_report()
    today_tx = db.get_today_transaction_count()

    # ── Metrics ──
    total_value = sum(it["มูลค่าคงเหลือ"] for it in items)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🗂️ สินค้าทั้งหมด", len(items))
    col2.metric("⚠️ ต่ำกว่ามาตรฐาน", len(restock))
    col3.metric("📝 Transactions วันนี้", today_tx)
    col4.metric("💰 มูลค่ารวม", f"฿{total_value:,.0f}")

    st.markdown("---")

    # ── Restock Alerts ──
    if restock:
        st.markdown("### 🔴 ต้องสั่งเพิ่ม")
        for item in restock:
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"**{item['รหัส']}** {item['รายการวัตถุดิบ']}")
                c2.markdown(f"คงเหลือ: **{item['คงเหลือจริง']:.1f}** {item['หน่วยนับ']}")
                c3.markdown(f"ขั้นต่ำ: **{item['สต็อกขั้นต่ำ']:.1f}** {item['หน่วยนับ']}")
                c4.markdown(
                    f'<span class="status-low">ต้องเติม {item["need_to_restock"]:.1f} {item["หน่วยนับ"]}</span>',
                    unsafe_allow_html=True,
                )
        st.markdown("---")
    else:
        if items:
            st.success("✅ สต็อกทุกรายการอยู่ในระดับปกติ!")
        st.markdown("---")

    # ── Full Stock Table ──
    st.markdown("### 📦 สต็อกทั้งหมด")
    if items:
        df = pd.DataFrame(items)
        display_cols = ["รหัส", "รายการวัตถุดิบ", "หมวดหมู่", "หน่วยนับ", "ราคา/หน่วย",
                        "สต็อกขั้นต่ำ", "คงเหลือจริง", "สถานะการสั่ง", "มูลค่าคงเหลือ", "อายุการเก็บ (วัน)"]
        df = df[[c for c in display_cols if c in df.columns]]

        def highlight_row(row):
            if "คงเหลือจริง" in row and "สต็อกขั้นต่ำ" in row:
                if row["คงเหลือจริง"] < row["สต็อกขั้นต่ำ"]:
                    return ["background-color: #fee2e2"] * len(row)
                elif row["คงเหลือจริง"] < row["สต็อกขั้นต่ำ"] * 1.2:
                    return ["background-color: #fef3c7"] * len(row)
            return ["background-color: #dcfce7"] * len(row)

        styled = df.style.apply(highlight_row, axis=1).format({
            "ราคา/หน่วย": "฿{:.0f}",
            "สต็อกขั้นต่ำ": "{:.1f}",
            "คงเหลือจริง": "{:.1f}",
            "มูลค่าคงเหลือ": "฿{:,.0f}",
        })
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีสินค้าในระบบ กรุณาเพิ่มที่เมนู **📦 จัดการ Stock**")


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 2 : จัดการ STOCK
# ═══════════════════════════════════════════════════════════════════════════

elif page == "📦 จัดการ Stock":
    st.markdown('<p class="page-header">📦 จัดการ Stock</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subheader">เพิ่ม แก้ไข หรือลบรายการวัตถุดิบ</p>', unsafe_allow_html=True)

    # ── Add new item ──
    st.markdown("### ➕ เพิ่มวัตถุดิบใหม่")
    st.info("💡 รหัสสินค้าจะถูกสร้างอัตโนมัติจากหมวดหมู่ (เช่น MT-0001 สำหรับเนื้อสัตว์)")
    with st.form("add_item_form", clear_on_submit=True):
        new_name = st.text_input("รายการวัตถุดิบ", placeholder="เช่น หมู: สันนอก / สันใน")

        ac3, ac4, ac5 = st.columns(3)
        new_category = ac3.selectbox("หมวดหมู่", CATEGORIES)
        new_unit = ac4.text_input("หน่วยนับ", placeholder="เช่น กก.")
        new_price = ac5.number_input("ราคา/หน่วย (฿)", min_value=0.0, step=10.0, value=0.0)

        ac6, ac7, ac8 = st.columns(3)
        new_min = ac6.number_input("สต็อกขั้นต่ำ", min_value=0.0, step=1.0, value=0.0)
        new_qty = ac7.number_input("จำนวนเริ่มต้น", min_value=0.0, step=1.0, value=0.0)
        new_shelf = ac8.number_input("อายุการเก็บ (วัน)", min_value=1, step=1, value=5)

        submitted = st.form_submit_button("✅ เพิ่มวัตถุดิบ", use_container_width=True)

        if submitted:
            if not new_name or not new_unit:
                st.error("❌ กรุณากรอกชื่อวัตถุดิบและหน่วยนับ")
            else:
                try:
                    code = db.add_item(new_name, new_category, new_unit,
                                new_price, new_min, new_qty, new_shelf)
                    st.success(f"✅ เพิ่ม **{code} — {new_name}** สำเร็จ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")

    st.markdown("---")

    # ── Existing items ──
    st.markdown("### 📋 รายการวัตถุดิบทั้งหมด")
    items = db.get_all_items()

    if not items:
        st.info("ยังไม่มีสินค้าในระบบ")
    else:
        for item in items:
            label = f"**{item['รหัส']}** {item['รายการวัตถุดิบ']} — {item['คงเหลือจริง']:.1f} {item['หน่วยนับ']} | {item['หมวดหมู่']}"
            with st.expander(label):
                with st.form(f"edit_{item['row_num']}"):
                    st.markdown(f"📌 รหัส: **{item['รหัส']}** *(สร้างอัตโนมัติ)*")
                    edit_name = st.text_input("ชื่อ", value=item["รายการวัตถุดิบ"], key=f"name_{item['row_num']}")

                    ec3, ec4, ec5 = st.columns(3)
                    cat_idx = CATEGORIES.index(item["หมวดหมู่"]) if item["หมวดหมู่"] in CATEGORIES else len(CATEGORIES) - 1
                    edit_cat = ec3.selectbox("หมวดหมู่", CATEGORIES, index=cat_idx, key=f"cat_{item['row_num']}")
                    edit_unit = ec4.text_input("หน่วย", value=item["หน่วยนับ"], key=f"unit_{item['row_num']}")
                    edit_price = ec5.number_input("ราคา/หน่วย", value=float(item["ราคา/หน่วย"]),
                                                   min_value=0.0, step=10.0, key=f"price_{item['row_num']}")

                    ec6, ec7 = st.columns(2)
                    edit_min = ec6.number_input("ขั้นต่ำ", value=float(item["สต็อกขั้นต่ำ"]),
                                                min_value=0.0, step=1.0, key=f"min_{item['row_num']}")
                    edit_shelf = ec7.number_input("อายุการเก็บ (วัน)", value=int(item["อายุการเก็บ (วัน)"]),
                                                   min_value=1, step=1, key=f"shelf_{item['row_num']}")

                    bc1, bc2 = st.columns(2)
                    save = bc1.form_submit_button("💾 บันทึก", use_container_width=True)
                    delete = bc2.form_submit_button("🗑️ ลบ", use_container_width=True)

                    if save:
                        db.update_item(item["row_num"], edit_name, edit_cat,
                                       edit_unit, edit_price, edit_min, edit_shelf)
                        st.success("✅ บันทึกแล้ว!")
                        st.rerun()
                    if delete:
                        db.delete_item(item["row_num"])
                        st.success("🗑️ ลบแล้ว!")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 3 : รับเข้า (Stock In)
# ═══════════════════════════════════════════════════════════════════════════

elif page == "➕ รับเข้า":
    st.markdown('<p class="page-header">➕ รับเข้า</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subheader">บันทึกการรับวัตถุดิบเข้าสต็อก</p>', unsafe_allow_html=True)

    items = db.get_all_items()

    if not items:
        st.warning("ยังไม่มีสินค้าในระบบ กรุณาเพิ่มสินค้าก่อน")
    else:
        item_options = {f"{it['รหัส']} — {it['รายการวัตถุดิบ']} ({it['คงเหลือจริง']:.1f} {it['หน่วยนับ']})": it for it in items}
        selected_label = st.selectbox("🔍 เลือกวัตถุดิบ", options=list(item_options.keys()), key="si_item")
        selected_item = item_options[selected_label]

        rc1, rc2 = st.columns(2)
        qty = rc1.number_input(
            f"จำนวนที่รับเข้า ({selected_item['หน่วยนับ']})",
            min_value=0.1, step=1.0, value=1.0, key="si_qty",
        )
        requester = rc2.text_input("👤 ผู้ทำรายการ", placeholder="เช่น a001", key="si_req")

        if st.button("➕ บันทึกรับเข้า", use_container_width=True, key="si_submit"):
            if qty <= 0:
                st.error("❌ กรุณาระบุจำนวนที่มากกว่า 0")
            elif not requester:
                st.error("❌ กรุณาระบุชื่อผู้ทำรายการ")
            else:
                order = db.add_transaction(
                    selected_item["รหัส"],
                    selected_item["รายการวัตถุดิบ"],
                    "รับเข้า",
                    qty,
                    selected_item["อายุการเก็บ (วัน)"],
                    requester,
                )
                st.success(f"✅ รับเข้า **{selected_item['รายการวัตถุดิบ']}** จำนวน **{qty:.1f} {selected_item['หน่วยนับ']}** — Order: {order}")
                st.rerun()

        # ── Today's stock-in ──
        st.markdown("---")
        st.markdown("### 📝 รายการรับเข้าวันนี้")
        today_txs = db.get_transactions(date_filter=db.thai_today(), tx_type="รับเข้า")
        if today_txs:
            df = pd.DataFrame(today_txs)
            df = df[["Order", "รหัส", "รายการ", "จำนวน", "life", "requestner"]]
            df.columns = ["Order", "รหัส", "รายการ", "จำนวน", "หมดอายุ", "ผู้ทำรายการ"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("ยังไม่มีรายการรับเข้าวันนี้")


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 4 : จ่ายออก (Stock Out)
# ═══════════════════════════════════════════════════════════════════════════

elif page == "🔻 จ่ายออก":
    st.markdown('<p class="page-header">🔻 จ่ายออก</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subheader">บันทึกการจ่ายวัตถุดิบออกจากสต็อก</p>', unsafe_allow_html=True)

    items = db.get_all_items()

    if not items:
        st.warning("ยังไม่มีสินค้าในระบบ กรุณาเพิ่มสินค้าก่อน")
    else:
        item_options = {f"{it['รหัส']} — {it['รายการวัตถุดิบ']} (คงเหลือ {it['คงเหลือจริง']:.1f} {it['หน่วยนับ']})": it for it in items}
        selected_label = st.selectbox("🔍 เลือกวัตถุดิบ", options=list(item_options.keys()), key="so_item")
        selected_item = item_options[selected_label]

        wc1, wc2 = st.columns(2)
        max_qty = float(selected_item["คงเหลือจริง"]) if selected_item["คงเหลือจริง"] > 0 else 0.1
        qty = wc1.number_input(
            f"จำนวนที่จ่ายออก ({selected_item['หน่วยนับ']})",
            min_value=0.1,
            max_value=max_qty,
            step=1.0,
            value=min(1.0, max_qty),
            key="so_qty",
        )
        requester = wc2.text_input("👤 ผู้ทำรายการ", placeholder="เช่น a002", key="so_req")

        if st.button("🔻 บันทึกจ่ายออก", use_container_width=True, key="so_submit"):
            if qty <= 0:
                st.error("❌ กรุณาระบุจำนวนที่มากกว่า 0")
            elif qty > selected_item["คงเหลือจริง"]:
                st.error(f"❌ จำนวนไม่เพียงพอ! คงเหลือเพียง {selected_item['คงเหลือจริง']:.1f} {selected_item['หน่วยนับ']}")
            elif not requester:
                st.error("❌ กรุณาระบุชื่อผู้ทำรายการ")
            else:
                order = db.add_transaction(
                    selected_item["รหัส"],
                    selected_item["รายการวัตถุดิบ"],
                    "จ่ายออก",
                    qty,
                    selected_item["อายุการเก็บ (วัน)"],
                    requester,
                )
                st.success(f"✅ จ่ายออก **{selected_item['รายการวัตถุดิบ']}** จำนวน **{qty:.1f} {selected_item['หน่วยนับ']}** — Order: {order}")
                st.rerun()

        # ── Today's stock-out ──
        st.markdown("---")
        st.markdown("### 📝 รายการจ่ายออกวันนี้")
        today_txs = db.get_transactions(date_filter=db.thai_today(), tx_type="จ่ายออก")
        if today_txs:
            df = pd.DataFrame(today_txs)
            df = df[["Order", "รหัส", "รายการ", "จำนวน", "requestner"]]
            df.columns = ["Order", "รหัส", "รายการ", "จำนวน", "ผู้ทำรายการ"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("ยังไม่มีรายการจ่ายออกวันนี้")


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 5 : TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════

elif page == "📋 Transactions":
    st.markdown('<p class="page-header">📋 Transactions</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subheader">ประวัติการเคลื่อนไหวของสต็อก (RP-PO)</p>', unsafe_allow_html=True)

    items = db.get_all_items()

    # ── Filters ──
    st.markdown("### 🔍 ตัวกรอง")
    fc1, fc2, fc3 = st.columns(3)

    filter_date = fc1.date_input("📅 วันที่", value=db.thai_today())

    filter_type = fc2.selectbox("📂 ประเภท", ["ทั้งหมด", "รับเข้า", "จ่ายออก"])
    filter_tx_type = None if filter_type == "ทั้งหมด" else filter_type

    item_filter_options = ["ทั้งหมด"] + [f"{it['รหัส']} — {it['รายการวัตถุดิบ']}" for it in items]
    filter_item_label = fc3.selectbox("📦 สินค้า", item_filter_options)
    filter_item_code = None
    if filter_item_label != "ทั้งหมด":
        filter_item_code = filter_item_label.split(" — ")[0].strip()

    st.markdown("---")

    # ── Transaction list ──
    transactions = db.get_transactions(
        date_filter=filter_date,
        tx_type=filter_tx_type,
        item_code=filter_item_code,
    )

    if transactions:
        total_in = sum(t["จำนวน"] for t in transactions if t["ประเภท"] == "รับเข้า")
        total_out = sum(t["จำนวน"] for t in transactions if t["ประเภท"] == "จ่ายออก")

        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("📝 รายการทั้งหมด", len(transactions))
        sc2.metric("➕ รับเข้า", f"{total_in:.1f}")
        sc3.metric("🔻 จ่ายออก", f"{total_out:.1f}")

        st.markdown("---")

        df = pd.DataFrame(transactions)
        display_cols = ["Approve", "Order", "วันที่", "รหัส", "รายการ", "ประเภท", "จำนวน", "อายุ", "life", "เวลาเหลือ", "requestner"]
        df = df[[c for c in display_cols if c in df.columns]]
        df.columns = ["อนุมัติ", "Order", "วันที่", "รหัส", "รายการ", "ประเภท", "จำนวน", "อายุ(วัน)", "หมดอายุ", "เหลือ(วัน)", "ผู้ทำรายการ"]

        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(f"ไม่พบรายการในวันที่ {filter_date.strftime('%d/%m/%Y')}")
