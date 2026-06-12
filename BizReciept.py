"""
BizTrack-OS Demo Receipt Generator
Streamlit app — generate branded prospect receipts instantly.
"""

import streamlit as st
import random, string, datetime, io, os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# ── Register fonts once ──
@st.cache_resource
def register_fonts():
    base = os.path.dirname(os.path.abspath(__file__))
    # Try every possible location
    candidates = [
        (os.path.join(base, "assets", "DejaVuSans.ttf"),
         os.path.join(base, "assets", "DejaVuSans-Bold.ttf")),
        (os.path.join(base, "fonts",  "DejaVuSans.ttf"),
         os.path.join(base, "fonts",  "DejaVuSans-Bold.ttf")),
        (os.path.join(base, "DejaVuSans.ttf"),
         os.path.join(base, "DejaVuSans-Bold.ttf")),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for reg, bold in candidates:
        if os.path.exists(reg) and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans",      reg))
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold",  bold))
                return True
            except Exception:
                continue
    return False

HAS_DEJAVU = register_fonts()
FONT       = "DejaVuSans"      if HAS_DEJAVU else "Helvetica"
FONT_BOLD  = "DejaVuSans-Bold" if HAS_DEJAVU else "Helvetica-Bold"

# Debug — remove after confirming fonts load
if not HAS_DEJAVU:
    st.warning("⚠️ DejaVu fonts not found — ₦ symbol may not render. "
               f"Looking in: {os.path.dirname(os.path.abspath(__file__))}")


def gen_sale_id():
    return "SL" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


def fmt_naira(amount):
    return f"\u20a6{amount:,.0f}"


def build_receipt(biz_name, customer, payment, items, sale_id, date_str) -> bytes:
    PAGE_W, PAGE_H = 297.638, 419.528
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    HEADER_BG   = colors.HexColor("#0D1B2A")
    GOLD        = colors.HexColor("#F5A623")
    WHITE       = colors.white
    DARK_TEXT   = colors.HexColor("#1A1A2E")
    MUTED       = colors.HexColor("#6B7A8D")
    BORDER_LINE = colors.HexColor("#D0D7E3")
    FOOTER_TEXT = colors.HexColor("#8B9BB4")

    MARGIN  = 20
    HEADER_H = 90

    # ── Header ──
    c.setFillColor(HEADER_BG)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)

    c.setFillColor(GOLD)
    c.setFont(FONT_BOLD, 18)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 32, biz_name.upper())

    c.setFillColor(WHITE)
    c.setFont(FONT, 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 50, date_str)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 65, f"Customer: {customer}")

    # ── Sale ID ──
    SALE_ROW_Y = PAGE_H - HEADER_H - 22
    c.setFillColor(MUTED);     c.setFont(FONT, 8)
    c.drawString(MARGIN, SALE_ROW_Y, "Sale ID")
    c.setFillColor(DARK_TEXT); c.setFont(FONT_BOLD, 8)
    c.drawRightString(PAGE_W - MARGIN, SALE_ROW_Y, sale_id)

    div_y = SALE_ROW_Y - 8
    c.setStrokeColor(BORDER_LINE); c.setLineWidth(0.5)
    c.line(MARGIN, div_y, PAGE_W - MARGIN, div_y)

    # ── Table header ──
    COL_ITEM  = MARGIN
    COL_QTY   = PAGE_W * 0.57
    COL_PRICE = PAGE_W * 0.73
    COL_TOTAL = PAGE_W - MARGIN

    TH_Y = div_y - 18
    c.setFillColor(DARK_TEXT); c.setFont(FONT_BOLD, 8.5)
    c.drawString(COL_ITEM,  TH_Y, "Item")
    c.drawRightString(COL_QTY,   TH_Y, "Qty")
    c.drawRightString(COL_PRICE, TH_Y, "Price")
    c.drawRightString(COL_TOTAL, TH_Y, "Total")

    # ── Item rows ──
    ROW_H  = 20
    cursor = TH_Y - ROW_H + 4
    c.setFont(FONT, 8.5)
    for item in items:
        line_total = item["qty"] * item["unit_price"]
        c.setFillColor(DARK_TEXT)
        c.drawString(COL_ITEM,  cursor, item["name"])
        c.drawRightString(COL_QTY,   cursor, str(item["qty"]))
        c.drawRightString(COL_PRICE, cursor, fmt_naira(item["unit_price"]))
        c.drawRightString(COL_TOTAL, cursor, fmt_naira(line_total))
        cursor -= ROW_H

    # ── Payment method ──
    PAY_Y = cursor - 6
    c.setStrokeColor(BORDER_LINE); c.setLineWidth(0.5)
    c.line(MARGIN, PAY_Y + 14, PAGE_W - MARGIN, PAY_Y + 14)
    c.setFillColor(MUTED);     c.setFont(FONT, 8)
    c.drawString(MARGIN, PAY_Y, "Payment method")
    c.setFillColor(DARK_TEXT); c.setFont(FONT_BOLD, 8)
    c.drawRightString(PAGE_W - MARGIN, PAY_Y, payment)

    # ── Total ──
    TOTAL_Y = PAY_Y - 28
    c.setStrokeColor(BORDER_LINE); c.setLineWidth(0.5)
    c.line(MARGIN, TOTAL_Y + 14, PAGE_W - MARGIN, TOTAL_Y + 14)
    c.setFillColor(DARK_TEXT); c.setFont(FONT_BOLD, 13)
    total = sum(i["qty"] * i["unit_price"] for i in items)
    c.drawCentredString(PAGE_W / 2, TOTAL_Y, f"Total  {fmt_naira(total)}")

    # ── Footer ──
    c.setStrokeColor(BORDER_LINE); c.setLineWidth(0.5)
    c.line(MARGIN, TOTAL_Y - 18, PAGE_W - MARGIN, TOTAL_Y - 18)
    c.setFillColor(FOOTER_TEXT)
    c.setFont(FONT, 8)
    c.drawCentredString(PAGE_W / 2, TOTAL_Y - 32, "Thank you for your purchase!")
    c.setFont(FONT, 7.5)
    c.drawCentredString(PAGE_W / 2, TOTAL_Y - 46, "Powered by BizTrack-OS")

    c.save()
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════
#  STREAMLIT UI
# ══════════════════════════════════════════════
st.set_page_config(page_title="BizTrack Receipt Generator", page_icon="🧾", layout="centered")

st.markdown("""
<style>
body, .stApp { background: #080B0F; color: #F0F4F8; }
h1, h2, h3 { color: #F5A623; }
.stTextInput > label, .stNumberInput > label,
.stSelectbox > label, .stDateInput > label { color: #8BA0B8 !important; font-size: 13px; }
.stButton > button {
    background: #F5A623; color: #080B0F; font-weight: 700;
    border: none; border-radius: 8px; padding: 10px 24px;
    width: 100%; font-size: 15px;
}
.stButton > button:hover { background: #C4831A; color: #fff; }
.stDownloadButton > button {
    background: #00C896; color: #080B0F; font-weight: 700;
    border: none; border-radius: 8px; padding: 10px 24px;
    width: 100%; font-size: 15px; margin-top: 8px;
}
div[data-testid="stExpander"] { background: #111827; border: 1px solid #1F2D3D; border-radius: 10px; }
hr { border-color: #1F2D3D; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🧾 BizTrack-OS Receipt Generator")
st.markdown("<p style='color:#8BA0B8;margin-top:-10px;'>Generate a branded demo receipt for any prospect — no account needed.</p>", unsafe_allow_html=True)
st.divider()

# ── Business details ──
st.markdown("#### Business Details")
col1, col2 = st.columns(2)
biz_name    = col1.text_input("Business Name", placeholder="e.g. Rabz Pharma")
customer    = col2.text_input("Customer Name", placeholder="e.g. Walk-in Customer")
payment     = st.selectbox("Payment Method", ["Cash", "POS", "Transfer"])
receipt_date = st.date_input("Receipt Date", value=datetime.date.today())
receipt_time = st.time_input("Receipt Time", value=datetime.datetime.now().time())

st.divider()

# ── Items ──
st.markdown("#### Items Sold")

if "item_rows" not in st.session_state:
    st.session_state.item_rows = [{"name": "", "qty": 1, "unit_price": 0}]

for i, item in enumerate(st.session_state.item_rows):
    c1, c2, c3, c4 = st.columns([4, 1, 2, 0.6])
    st.session_state.item_rows[i]["name"]       = c1.text_input("Item name",   value=item["name"],       key=f"name_{i}",  label_visibility="collapsed", placeholder=f"Product name")
    st.session_state.item_rows[i]["qty"]        = c2.number_input("Qty",       value=item["qty"],        key=f"qty_{i}",   label_visibility="collapsed", min_value=1)
    st.session_state.item_rows[i]["unit_price"] = c3.number_input("Unit price",value=item["unit_price"], key=f"price_{i}", label_visibility="collapsed", min_value=0, step=100)
    if c4.button("✕", key=f"del_{i}", help="Remove item") and len(st.session_state.item_rows) > 1:
        st.session_state.item_rows.pop(i)
        st.rerun()

if st.button("＋ Add another item"):
    st.session_state.item_rows.append({"name": "", "qty": 1, "unit_price": 0})
    st.rerun()

# ── Total preview ──
total = sum(it["qty"] * it["unit_price"] for it in st.session_state.item_rows)
st.markdown(f"<p style='text-align:right;font-size:18px;font-weight:700;color:#F5A623;'>Total: ₦{total:,.0f}</p>", unsafe_allow_html=True)

st.divider()

# ── Generate ──
if st.button("🧾 Generate Receipt"):
    if not biz_name.strip():
        st.error("Please enter the business name.")
    elif not any(it["name"].strip() for it in st.session_state.item_rows):
        st.error("Please add at least one item.")
    else:
        date_str  = f"{receipt_date.strftime('%-d %b %Y')} · {receipt_time.strftime('%H:%M')}"
        sale_id   = gen_sale_id()
        items     = [it for it in st.session_state.item_rows if it["name"].strip() and it["unit_price"] > 0]
        pdf_bytes = build_receipt(
            biz_name.strip(),
            customer.strip() or "Walk-in Customer",
            payment,
            items,
            sale_id,
            date_str
        )
        st.session_state["pdf_bytes"]  = pdf_bytes
        st.session_state["pdf_name"]   = biz_name.strip().replace(" ", "_")
        st.session_state["sale_id"]    = sale_id
        st.success(f"✅ Receipt generated! Sale ID: {sale_id}")

if "pdf_bytes" in st.session_state:
    st.download_button(
        label="⬇️ Download Receipt PDF",
        data=st.session_state["pdf_bytes"],
        file_name=f"receipt_{st.session_state['pdf_name']}.pdf",
        mime="application/pdf"
)
