from __future__ import annotations
import os
from datetime import datetime
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
GS_WEBAPP_URL = os.getenv("GS_WEBAPP_URL")
PAGE_SIZE = 8



# ===================== DATA: SEGMENT -> JENIS ORDER =====================
SEGMENT_ORDERS = {
    "Assurance B2B Eksternal": [
        "Aktivasi Cross Connect TDE",
        "Aktivasi/Migrasi/Dismantel DCS",
        "Aktivasi/Migrasi/Dismantel Digiserve",
        "Aktivasi/Migrasi/Dismantel Hypernet",
        "Corrective Akses Tower CENTRATAMA",
        "Corrective Akses Tower Lintasarta",
        "Corrective Akses Tower UMT",
        "Corrective Cross Connect TDE",
        "Corrective CSA",
        "Corrective DCS",
        "Corrective Digiserve",
        "Corrective Hypernet",
        "Corrective MMP",
        "Corrective MyRep",
        "Corrective NuTech",
        "Corrective SNT",
        "Corrective SPBU",
        "Corrective TBG",
        "Corrective Tower POLARIS",
        "Corrective Tower TIS",
        "Inventory SPBU",
        "Preventif MMP",
        "Preventive Akses Tower CENTRATAMA",
        "Preventive Akses Tower Lintasarta",
        "Preventive Akses Tower UMT",
        "Preventive Asianet",
        "Preventive CSA",
        "Preventive NuTech",
        "Preventive SPBU",
        "Preventive TBG",
        "Preventive Tower POLARIS",
        "Preventive Tower TIS",
        "Relokasi DCS",
        "Relokasi Digiserve",
        "Relokasi Hypernet",
        "Corrective Mitratel",
    ],
    "Assurance B2B Internal": [
        "HSI Indihome Reseller",
        "Tangible",
        "Tiket Datin Kategori 1",
        "Tiket Datin Kategori 2",
        "Tiket Datin Kategori 3",
        "Tiket HSI Indibiz",
        "Tiket NodeB CNQ (Preventive/Quality)",
        "Tiket NodeB Critical",
        "Tiket NodeB Low",
        "Tiket NodeB Major",
        "Tiket NodeB Minor",
        "Tiket NodeB Premium",
        "Tiket NodeB Premium Preventive",
        "Tiket OLO Datin Gamas",
        "Tiket OLO Datin Non Gamas",
        "Tiket OLO Datin Quality",
        "Tiket OLO SL WDM",
        "Tiket OLO SL WDM Quality",
        "Tiket Pra SQM Gaul HSI",
        "Tiket SIP Trunk",
        "Tiket SQM Datin",
        "Tiket SQM HSI",
        "Tiket WIFI ID",
        "Tiket Wifi Logic",
        "Unspec DATIN",
        "Unspec HSI",
        "Unspec SITE",
        "Unspec WIFI",
        "Validasi Data EBIS",
        "Validasi Data WIFI",
    ],
    "Assurance B2C": [
        "Dismantling DC",
        "Infracare",
        "IXSA FTM",
        "IXSA ODC",
        "IXSA OLT",
        "Lapsung (Laporan Langsung)",
        "Patroli Akses",
        "SQM Reguler",
        "Tangible ODP",
        "Tiket GAMAS DISTRIBUSI",
        "Tiket GAMAS FEEDER",
        "Tiket GAMAS ODC",
        "Tiket GAMAS ODP",
        "Tiket Reguler VVIP",
        "Tiket Reguler Diamond",
        "Unspec Reguler",
        "Validasi Tiang",
        "Valins FTM",
        "Valins ODC",
        "Valins Regular",
    ],
    "Provisioning B2B": [
        "Dismantling NTE B2B",
        "PSB DATIN",
        "PSB INDIBIZ",
        "PSB OLO",
        "PSB WIFI",
        "Tiket FFG DATIN",
        "Tiket FFG HSI",
        "Tiket FFG WIFI",
    ],
    "Provisioning B2B Eksternal": [
        "Preventive Fiberisasi",
        "PSB MyRep",
        "PSB Surge",
    ],
    "Provisioning B2C": [
        "DISMANTLING ONT",
        "DISMANTLING PLC",
        "DISMANTLING STB",
        "DISMANTLING WIFI EXTENDER",
        "DISMANTLING FWA",
        "PDA",
        "PSB Indihome",
        "REPLACEMENT ONT Premium/Dual Band",
        "REPLACEMENT STB",
        "Tiket FFG Indihome",
    ],
}

SEGMENTS = list(SEGMENT_ORDERS.keys())

ASSURANCE_SEGMENTS = {"Assurance B2B Internal", "Assurance B2B Eksternal", "Assurance B2C"}
PROVISIONING_SEGMENTS = {"Provisioning B2B", "Provisioning B2B Eksternal", "Provisioning B2C"}


# ===================== FORM RULES =====================
def tiket_optional(jenis_order: str) -> bool:
    s = (jenis_order or "").lower()
    return ("tangible" in s) or ("ixsa" in s) or ("unspec" in s)


def fields_for_segment(segment: str):
    if segment in ASSURANCE_SEGMENTS:
        return ["service_no", "tiket_no", "labor1", "labor2", "start_dt", "close_dt", "workzone"]
    else:
        return ["service_no", "order_no", "labor1", "labor2", "start_dt", "close_dt", "workzone"]


PROMPTS = {
    "service_no": "Isi **service no**:",
    "tiket_no": "Isi **tiket no** (kalau tidak ada untuk Tangible/IXSA/Unspec, ketik `-`):",
    "order_no": "Isi **order no**:",
    "labor1": "Isi **labor code teknisi 1**:",
    "labor2": "Isi **labor code teknisi 2** (kalau tidak ada, ketik `-`):",
    "start_dt": "Isi **tanggal jam start** format `DD/MM/YYYY HH:MM` (contoh: `03/02/2026 08:30`):",
    "close_dt": "Isi **tanggal jam close** format `DD/MM/YYYY HH:MM` (contoh: `03/02/2026 17:10`):",
    "workzone": "Isi **workzone**:",
}


def parse_dt(s: str):
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        return None


def form_active(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(context.user_data.get("form_active"))


def clear_form(context: ContextTypes.DEFAULT_TYPE):
    for k in [
        "form_active",
        "form_segment",
        "form_order",
        "form_fields",
        "form_step",
        "form_answers",
        "form_page",
        "pending_payload",   # ⬅️ INI YANG DITAMBAHKAN
    ]:
        context.user_data.pop(k, None)



def start_form(context: ContextTypes.DEFAULT_TYPE, segment: str, jenis_order: str, page: int):
    context.user_data["form_active"] = True
    context.user_data["form_segment"] = segment
    context.user_data["form_order"] = jenis_order
    context.user_data["form_fields"] = fields_for_segment(segment)
    context.user_data["form_step"] = 0
    context.user_data["form_answers"] = {}
    context.user_data["form_page"] = page


# ===================== KEYBOARDS =====================
def segment_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(seg, callback_data=f"SEG|{seg}|0")] for seg in SEGMENTS])


def orders_keyboard(segment: str, page: int):
    orders = SEGMENT_ORDERS.get(segment, [])
    total = len(orders)
    max_page = (total - 1) // PAGE_SIZE if total else 0
    page = max(0, min(page, max_page))

    start = page * PAGE_SIZE
    chunk = orders[start : start + PAGE_SIZE]

    rows = []
    for i, order_name in enumerate(chunk):
        idx = start + i
        rows.append([InlineKeyboardButton(order_name, callback_data=f"ORD|{segment}|{idx}|{page}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"SEG|{segment}|{page-1}"))
    nav.append(InlineKeyboardButton("🏠 Segment", callback_data="HOME"))
    if page < max_page:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"SEG|{segment}|{page+1}"))
    rows.append(nav)

    return InlineKeyboardMarkup(rows)


def confirm_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ SIMPAN", callback_data="CONFIRM_SAVE"),
            InlineKeyboardButton("❌ BATAL", callback_data="CONFIRM_CANCEL"),
        ]
    ])


# ===================== BOT FLOW =====================
async def ask_next_question(chat_id: int, context: ContextTypes.DEFAULT_TYPE, bot):
    step = context.user_data["form_step"]
    fields = context.user_data["form_fields"]

    if step >= len(fields):
        await finish_form(chat_id, context, bot)
        return

    field = fields[step]
    prompt = PROMPTS[field]
    await bot.send_message(
        chat_id=chat_id,
        text=prompt + "\n\nKetik /cancel untuk membatalkan.",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown",
    )


async def finish_form(chat_id: int, context: ContextTypes.DEFAULT_TYPE, bot):

    segment = context.user_data["form_segment"]
    jenis_order = context.user_data["form_order"]
    ans = context.user_data["form_answers"]
    user_id = context.user_data.get("telegram_user_id", "")

    tiket_no = (ans.get("tiket_no") or "").strip()
    order_no = (ans.get("order_no") or "").strip()

    if tiket_no == "-":
        tiket_no = ""
    if order_no == "-":
        order_no = ""

    payload = {
        "timestamp_input": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "telegram_user_id": str(user_id),
        "segment": segment,
        "jenis_order": jenis_order,
        "service_no": ans.get("service_no", "").strip(),
        "tiket_no": tiket_no,
        "order_no": order_no,
        "labor_code_teknisi_1": ans.get("labor1", "").strip(),
        "labor_code_teknisi_2": ans.get("labor2", "").strip(),
        "start_dt": ans.get("start_dt", "").strip(),
        "close_dt": ans.get("close_dt", "").strip(),
        "workzone": ans.get("workzone", "").strip(),
    }

    # ⬅️ SIMPAN SEMENTARA (BELUM KIRIM KE SHEET)
    context.user_data["pending_payload"] = payload

    summary = (
        "📋 **MOHON KONFIRMASI DATA**\n\n"
        f"**Segment:** {segment}\n"
        f"**Jenis Order:** {jenis_order}\n\n"
        f"service no: {payload['service_no']}\n"
        f"tiket no: {payload['tiket_no']}\n"
        f"order no: {payload['order_no']}\n"
        f"labor code teknisi 1: {payload['labor_code_teknisi_1']}\n"
        f"labor code teknisi 2: {payload['labor_code_teknisi_2']}\n"
        f"tanggal jam start: {payload['start_dt']}\n"
        f"tanggal jam close: {payload['close_dt']}\n"
        f"workzone: {payload['workzone']}\n\n"
        "Apakah data ini sudah benar?"
    )

    await bot.send_message(
        chat_id=chat_id,
        text=summary,
        reply_markup=confirm_keyboard(),
        parse_mode="Markdown",
    )


# ===================== COMMANDS =====================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_form(context)
    await update.message.reply_text("Silakan pilih **Segment**:", reply_markup=segment_keyboard(), parse_mode="Markdown")


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if form_active(context):
        await update.message.reply_text("Kamu sedang input data. Ketik /cancel dulu untuk batalkan, lalu /menu.")
        return
    await update.message.reply_text("Silakan pilih **Segment**:", reply_markup=segment_keyboard(), parse_mode="Markdown")


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if form_active(context):
        clear_form(context)
        await update.message.reply_text("✅ Input dibatalkan. Ketik /menu untuk mulai lagi.")
    else:
        await update.message.reply_text("Tidak ada input aktif. Ketik /menu untuk mulai.")


# ===================== BUTTON HANDLER =====================
async def on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    # ===== Konfirmasi sebelum simpan =====
    if q.data == "CONFIRM_SAVE":
        payload = context.user_data.get("pending_payload")
        if not payload:
            await q.edit_message_text("⚠️ Data tidak ditemukan. Ketik /menu untuk ulang.")
            return

        try:
            r = requests.post(GS_WEBAPP_URL, json=payload, timeout=15)
            if r.status_code == 200:
                await q.edit_message_text("✅ Data BERHASIL disimpan ke Google Sheet.")
            else:
                await q.edit_message_text(f"⚠️ Gagal simpan ke Google Sheet (HTTP {r.status_code}).")
        except Exception as e:
            await q.edit_message_text(f"⚠️ Error kirim data: {e}")

        context.user_data.pop("pending_payload", None)
        clear_form(context)
        return

    if q.data == "CONFIRM_CANCEL":
        context.user_data.pop("pending_payload", None)
        clear_form(context)
        await q.edit_message_text("❌ Input dibatalkan. Ketik /menu untuk mulai ulang.")
        return
    if q.data == "CANCEL_FORM":
        clear_form(context)
        await q.edit_message_text("✅ Input dibatalkan. Ketik /menu untuk mulai lagi.")
        return

    if q.data == "HOME":
        clear_form(context)
        await q.edit_message_text("Silakan pilih **Segment**:", reply_markup=segment_keyboard(), parse_mode="Markdown")
        return

    if q.data.startswith("SEG|"):
        _, segment, page_str = q.data.split("|", 2)
        page = int(page_str)
        total = len(SEGMENT_ORDERS.get(segment, []))
        max_page = (total - 1) // PAGE_SIZE if total else 0
        text = f"**Segment:** {segment}\nPilih Jenis Order (Hal {page+1}/{max_page+1})"
        await q.edit_message_text(text, reply_markup=orders_keyboard(segment, page), parse_mode="Markdown")
        return

    if q.data.startswith("ORD|"):
        _, segment, idx_str, page_str = q.data.split("|", 3)
        idx = int(idx_str)
        page = int(page_str)

        orders = SEGMENT_ORDERS.get(segment, [])
        if not (0 <= idx < len(orders)):
            await q.edit_message_text("Pilihan order tidak valid. Ketik /menu untuk ulang.")
            return

        jenis_order = orders[idx]

        # mulai form
        start_form(context, segment, jenis_order, page)

        # simpan user id untuk payload
        context.user_data["telegram_user_id"] = update.effective_user.id if update.effective_user else ""

        await q.edit_message_text(
            f"✅ Dipilih:\nSegment: {segment}\nJenis Order: {jenis_order}\n\n"
            "Sekarang isi data satu per satu.\n"
            "Ketik /cancel untuk membatalkan."
        )

        await ask_next_question(q.message.chat_id, context, context.bot)
        return


# ===================== TEXT INPUT HANDLER =====================
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not form_active(context):
        await update.message.reply_text("Ketik /menu untuk mulai pilih Segment & Jenis Order.")
        return

    text = (update.message.text or "").strip()

    step = context.user_data["form_step"]
    fields = context.user_data["form_fields"]
    field = fields[step]

    segment = context.user_data.get("form_segment", "")
    jenis_order = context.user_data.get("form_order", "")

    # ----- Validasi per field -----
    if field in ("start_dt", "close_dt"):
        dt = parse_dt(text)
        if not dt:
            await update.message.reply_text("Format salah. Gunakan `DD/MM/YYYY HH:MM` (contoh `03/02/2026 08:30`).")
            return
        context.user_data["form_answers"][field] = dt.strftime("%d/%m/%Y %H:%M")

    elif field == "labor2":
        context.user_data["form_answers"][field] = "" if text == "-" else text

    elif field == "tiket_no":
        # tiket boleh kosong untuk Tangible/IXSA/Unspec (Assurance)
        if text == "-" or text == "":
            if segment in ASSURANCE_SEGMENTS and tiket_optional(jenis_order):
                context.user_data["form_answers"][field] = ""  # boleh kosong
            else:
                await update.message.reply_text("Tiket no tidak boleh kosong untuk order ini. Isi tiket no.")
                return
        else:
            context.user_data["form_answers"][field] = text

    else:
        if text == "":
            await update.message.reply_text("Tidak boleh kosong. Silakan isi lagi.")
            return
        context.user_data["form_answers"][field] = text

    # Cek logika waktu: close >= start
    ans = context.user_data["form_answers"]
    if "start_dt" in ans and "close_dt" in ans:
        s = parse_dt(ans["start_dt"])
        c = parse_dt(ans["close_dt"])
        if s and c and c < s:
            await update.message.reply_text("Tanggal close tidak boleh lebih awal dari start. Isi **tanggal jam close** lagi.")
            # paksa balik ke close_dt
            context.user_data["form_step"] = fields.index("close_dt")
            return

    # ----- next step -----
    context.user_data["form_step"] += 1
    await ask_next_question(update.effective_chat.id, context, context.bot)


# ===================== MAIN =====================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))

    app.add_handler(CallbackQueryHandler(on_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    print("✅ Bot sedang berjalan... tekan Ctrl+C untuk berhenti.")
    app.run_polling()


if __name__ == "__main__":
    main()

