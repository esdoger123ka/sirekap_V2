from __future__ import annotations

import os
import re
import sqlite3
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
GS_CAPAIAN_URL = os.getenv("GS_CAPAIAN_URL", GS_WEBAPP_URL)
PAGE_SIZE = 8
DB_PATH = os.getenv("BOT_DB_PATH", "bot_data.db")


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
        "Tiket Reguler",
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
        "FTTR IBU",
        "SPPG",
        "PSB Surge",
    ],
    "Provisioning B2C": [
        "DISMANTLING ONT",
        "DISMANTLING PLC",
        "DISMANTLING STB",
        "DISMANTLING WIFI EXTENDER",
        "DISMANTLING FWA",
        "PDA",
        "ORBIT",
        "PSB Indihome",
        "REPLACEMENT ONT Premium/Dual Band",
        "Survey PT2",
        "Progress PT2",
        "REPLACEMENT STB",
        "Tiket FFG Indihome",
    ],
}

SEGMENTS = list(SEGMENT_ORDERS.keys())

ASSURANCE_SEGMENTS = {"Assurance B2B Internal", "Assurance B2B Eksternal", "Assurance B2C"}
PROVISIONING_SEGMENTS = {"Provisioning B2B", "Provisioning B2B Eksternal", "Provisioning B2C"}


# ===================== BOBOT / MAN HOURS =====================
# Sumber dari user; jenis order yang tidak terdefinisi dianggap 0.
ORDER_MAN_HOURS = {
    # Assurance B2B Eksternal
    "Aktivasi Cross Connect TDE": 4.0,
    "Aktivasi/Migrasi/Dismantel DCS": 4.0,
    "Aktivasi/Migrasi/Dismantel Digiserve": 4.0,
    "Aktivasi/Migrasi/Dismantel Hypernet": 4.0,
    "Corrective Akses Tower CENTRATAMA": 4.0,
    "Corrective Akses Tower Lintasarta": 4.0,
    "Corrective Akses Tower UMT": 4.0,
    "Corrective Cross Connect TDE": 4.0,
    "Corrective CSA": 4.0,
    "Corrective DCS": 4.0,
    "Corrective Digiserve": 4.0,
    "Corrective Hypernet": 4.0,
    "Corrective MMP": 4.0,
    "Corrective MyRep": 4.0,
    "Corrective NuTech": 2.0,
    "Corrective SNT": 4.0,
    "Corrective SPBU": 4.0,
    "Corrective TBG": 4.0,
    "Corrective Tower POLARIS": 4.0,
    "Corrective Tower TIS": 4.0,
    "Inventory SPBU": 4.0,
    "Preventif MMP": 2.0,
    "Preventive Akses Tower CENTRATAMA": 2.0,
    "Preventive Akses Tower Lintasarta": 2.0,
    "Preventive Akses Tower UMT": 2.0,
    "Preventive Asianet": 2.67,
    "Preventive CSA": 2.0,
    "Preventive NuTech": 2.0,
    "Preventive SPBU": 4.0,
    "Preventive TBG": 2.0,
    "Preventive Tower POLARIS": 2.0,
    "Preventive Tower TIS": 2.0,
    "Relokasi DCS": 1.0,
    "Relokasi Digiserve": 1.0,
    "Relokasi Hypernet": 1.0,
    "Corrective Mitratel": 4.0,
    # Assurance B2B Internal
    "HSI Indihome Reseller": 2.0,
    "Tiket Datin Kategori 1": 2.67,
    "Tiket Datin Kategori 2": 2.67,
    "Tiket Datin Kategori 3": 2.67,
    "Tiket HSI Indibiz": 2.0,
    "Tiket NodeB CNQ (Preventive/Quality)": 4.0,
    "Tiket NodeB Critical": 6.0,
    "Tiket NodeB Low": 4.0,
    "Tiket NodeB Major": 4.0,
    "Tiket NodeB Minor": 4.0,
    "Tiket NodeB Premium": 6.0,
    "Tiket NodeB Premium Preventive": 4.0,
    "Tiket OLO Datin Gamas": 4.0,
    "Tiket OLO Datin Non Gamas": 4.0,
    "Tiket OLO Datin Quality": 4.0,
    "Tiket OLO SL WDM": 4.0,
    "Tiket OLO SL WDM Quality": 4.0,
    "Tiket Pra SQM Gaul HSI": 2.0,
    "Tiket SIP Trunk": 2.67,
    "Tiket SQM Datin": 2.67,
    "Tiket SQM HSI": 2.0,
    "Tiket WIFI ID": 2.67,
    "Tiket Wifi Logic": 2.67,
    "Unspec DATIN": 2.67,
    "Unspec HSI": 2.0,
    "Unspec SITE": 2.0,
    "Unspec WIFI": 2.0,
    # Assurance B2C
    "Dismantling DC": 1.0,
    "Infracare": 2.0,
    "IXSA FTM": 4.0,
    "IXSA ODC": 4.0,
    "IXSA OLT": 2.0,
    "Lapsung (Laporan Langsung)": 2.0,
    "SQM Reguler": 2.0,
    "Tangible ODP": 2.0,
    "Tiket Reguler": 2.0,
    "Unspec Reguler": 2.0,
    "Validasi Tiang": 0.3,
    "Valins FTM": 4.0,
    "Tiket GAMAS DISTRIBUSI": 4.0,
    "Tiket GAMAS FEEDER": 10.0,
    "Tiket GAMAS ODC": 18.0,
    "Tiket GAMAS ODP": 3.0,
    "Valins ODC": 4.0,
    "Valins Regular": 0.5,
    # Provisioning B2B
    "PSB INDIBIZ": 5.3,
    "PSB OLO": 6.3,
    "PSB WIFI": 6.3,
    "Tiket FFG DATIN": 2.0,
    "Tiket FFG HSI": 2.0,
    "Tiket FFG WIFI": 2.0,
    # Provisioning B2B Eksternal
    "Preventive Fiberisasi": 2.0,
    "PSB MyRep": 2.0,
    "PSB Surge": 2.0,
    "FTTR IBU": 5.0,
    "SPPG": 4.0,
    # Provisioning B2C
    "DISMANTLING ONT": 0.67,
    "DISMANTLING PLC": 0.67,
    "DISMANTLING STB": 0.67,
    "DISMANTLING WIFI EXTENDER": 0.67,
    "DISMANTLING FWA": 0.67,
    "PDA": 5.3,
    "ORBIT": 1.1,
    "PSB Indihome": 5.3,
    "REPLACEMENT ONT Premium/Dual Band": 1.33,
    "REPLACEMENT STB": 1.33,
    "Tiket FFG Indihome": 2.0,
    "Survey PT2": 1.5,
    "Progress PT2": 2.0,
}


def man_hours_for_order(jenis_order: str) -> float:
    return float(ORDER_MAN_HOURS.get(jenis_order, 0.0))


def month_key_from_dt(dt_str: str) -> str:
    dt = parse_dt(dt_str or "")
    if not dt:
        dt = datetime.now()
    return dt.strftime("%m/%Y")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id TEXT,
                labor_code TEXT NOT NULL,
                teknisi_name TEXT,
                segment TEXT,
                jenis_order TEXT,
                close_dt TEXT,
                month_key TEXT,
                man_hours REAL NOT NULL,
                timestamp_input TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_credits_labor_month ON job_credits (labor_code, month_key)")
        conn.commit()


def save_job_credits(payload: dict):
    month_key = month_key_from_dt(payload.get("close_dt", ""))
    mh = float(payload.get("man_hours_order", 0.0) or 0.0)
    rows = []

    if payload.get("labor_code_teknisi_1"):
        rows.append(
            (
                str(payload.get("telegram_user_id", "")),
                payload.get("labor_code_teknisi_1", ""),
                payload.get("nama_teknisi_1", ""),
                payload.get("segment", ""),
                payload.get("jenis_order", ""),
                payload.get("close_dt", ""),
                month_key,
                mh,
                payload.get("timestamp_input", ""),
            )
        )

    if payload.get("labor_code_teknisi_2"):
        rows.append(
            (
                str(payload.get("telegram_user_id", "")),
                payload.get("labor_code_teknisi_2", ""),
                payload.get("nama_teknisi_2", ""),
                payload.get("segment", ""),
                payload.get("jenis_order", ""),
                payload.get("close_dt", ""),
                month_key,
                mh,
                payload.get("timestamp_input", ""),
            )
        )

    if not rows:
        return

    with get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO job_credits (
                telegram_user_id, labor_code, teknisi_name, segment, jenis_order,
                close_dt, month_key, man_hours, timestamp_input
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


def _is_month_arg(text: str) -> bool:
    return bool(re.fullmatch(r"(0[1-9]|1[0-2])/\d{4}", text or ""))


def get_monthly_summary(labor_code: str, month_key: str)
    with get_conn() as conn:
        total_row = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(man_hours), 0)
            FROM job_credits
            WHERE labor_code = ? AND month_key = ?
            """,
            (labor_code, month_key),
        ).fetchone()

        detail_rows = conn.execute(
            """
            SELECT jenis_order, COUNT(*) AS total_job, COALESCE(SUM(man_hours), 0) AS total_mh
            FROM job_credits
            WHERE labor_code = ? AND month_key = ?
            GROUP BY jenis_order
            ORDER BY total_mh DESC, total_job DESC, jenis_order ASC
            """,
            (labor_code, month_key),
        ).fetchall()

    return total_row, detail_rows


def get_monthly_summary_from_sheet(labor_code: str, month_key: str):
    """
    Ambil data capaian dari Google Apps Script (doGet).
    Endpoint diharapkan menerima query:
      ?action=capaian&labor_code=<...>&month=<MM/YYYY>
    dan merespon JSON:
      {
        "ok": true,
        "total_job": 10,
        "total_mh": 24.5,
        "details": [
          {"jenis_order": "PSB Indihome", "total_job": 3, "total_mh": 15.9}
        ]
      }
    """
    if not GS_CAPAIAN_URL:
        raise RuntimeError("GS_CAPAIAN_URL/GS_WEBAPP_URL belum diset di environment.")

    resp = requests.get(
        GS_CAPAIAN_URL,
        params={
            "action": "capaian",
            "labor_code": labor_code,
            "month": month_key,
        },
        timeout=20,
    )
    resp.raise_for_status()

    payload = resp.json()
    if not payload.get("ok"):
        raise RuntimeError(payload.get("error") or "Respons Apps Script tidak valid.")

    total_job = int(payload.get("total_job", 0) or 0)
    total_mh = float(payload.get("total_mh", 0) or 0)

    details = payload.get("details", []) or []
    detail_rows = []
    for row in details:
        jenis_order = str(row.get("jenis_order", "") or "")
        job_count = int(row.get("total_job", 0) or 0)
        mh_sum = float(row.get("total_mh", 0) or 0)
        detail_rows.append((jenis_order, job_count, mh_sum))

    return (total_job, total_mh), detail_rows


# ===================== TEKNISI (MENU PILIH) =====================
TECH_UNITS = {
    "Assurance B2C": [
        {"name": "MAKARIUS SUMIARSO", "labor": "74130340"},
        {"name": "LUTHFI FATURAHMAN", "labor": "94150197"},
        {"name": "SEPTIAN MAULUDIN", "labor": "92150306"},
        {"name": "GISA TAKWA MARCEL", "labor": "20971385"},
        {"name": "MUCHAMAD RIDWAN", "labor": "94159890"},
        {"name": "YOGI SETIAWAN", "labor": "89170014"},
        {"name": "NUGROHO EDI SUSANTO", "labor": "87155938"},
        {"name": "BENY SOMANTRI", "labor": "20740013"},
        {"name": "FIRMAN FUJI KHOMIRUN", "labor": "18870008"},
        {"name": "ARIFIN SURIFIN", "labor": "18720002"},
        {"name": "AHMAD RANGGA MUZAKKI", "labor": "21000004"},
        {"name": "IQBAL FAUZI", "labor": "99170252"},
        {"name": "ENJANG ABDUL HAMID", "labor": "80152394"},
        {"name": "RENDY JUNTARA", "labor": "93150362"},
        {"name": "YUDHA AFRIZAL", "labor": "18940455"},
        {"name": "AJI WAHYU APRIADI", "labor": "94150205"},
        {"name": "RIZA ABURIZAL FAUZI", "labor": "20950971"},
        {"name": "AHMAD GHANDI SYUKRUDIN", "labor": "90160119"},
        {"name": "SANDI RAHMADI", "labor": "95160280"},
        {"name": "HENDRA SETIAWAN", "labor": "18840043"},
        {"name": "DIKI SODIKIN", "labor": "18980373"},
        {"name": "TRI DIAN", "labor": "84151814"},
        {"name": "DWI PUTRA YULIANTO", "labor": "21010001"},
        {"name": "CECEP ENDI KURNIA", "labor": "97150195"},
        {"name": "MUHAMAD FEBRY INDRA", "labor": "99170282"},
        {"name": "ALDY ARDIANSYAH", "labor": "95155941"},
        {"name": "SETIO PRAMONO", "labor": "18840003"},
        {"name": "HENDRA SURYANA", "labor": "18780003"},
    ],
    "Provisioning B2C": [
        {"name": "ADJI FIRMANSYAH", "labor": "18990315"},
        {"name": "AGUNG HARDIYANTO", "labor": "18980502"},
        {"name": "AHMAD RIZAL", "labor": "98170695"},
        {"name": "AHMAD ZATNIKA", "labor": "21940017"},
        {"name": "ALDI ALFAUZI", "labor": "22990054"},
        {"name": "ALVINO MAULANA PUTRA", "labor": "97156163"},
        {"name": "ARIF BUDIMAN", "labor": "18970322"},
        {"name": "ARVAN MAULANA", "labor": "22000240"},
        {"name": "BILLY ZULFIKAR", "labor": "20950686"},
        {"name": "CAHYO JALU PRASETOYO", "labor": "20970046"},
        {"name": "EDO RAMDANI", "labor": "25000028"},
        {"name": "FIRMAN MAULANA YUSUF", "labor": "19980260"},
        {"name": "GALIH PRIANDANI", "labor": "25910063"},
        {"name": "GANDI GALIH", "labor": "20800025"},
        {"name": "HANIF FARHAN MUTAQIN", "labor": "20880157"},
        {"name": "HENDRA GUNAWAN", "labor": "18940040"},
        {"name": "HENDRIAWAN", "labor": "20960831"},
        {"name": "MUHAMMAD ANGGA N", "labor": "20970053"},
        {"name": "MUHAMMAD SYAMSUL BAHRI", "labor": "21970031"},
        {"name": "NOVA MUCHLIS", "labor": "18870084"},
        {"name": "PUJI SANTOSO", "labor": "18820045"},
        {"name": "RENGGI NUGRAHA", "labor": "20940711"},
        {"name": "RIFKY FAJAR F", "labor": "25970117"},
        {"name": "RISMAN FAUZI", "labor": "18940108"},
        {"name": "RIZKY GUNAWAN", "labor": "20950982"},
        {"name": "SHANDIKA DWI PUTRA", "labor": "25060099"},
        {"name": "TAUFIK ISMAIL", "labor": "18980367"},
        {"name": "VERDIAN A", "labor": "21000006"},
        {"name": "MOH WILDAN FIRDAUS", "labor": "18980509"},
        {"name": "WISNU HIDAYAT", "labor": "20971476"},
        {"name": "YOGI SEPTIANDI", "labor": "19910031"},
        {"name": "NUR FUAD S", "labor": "18990319"},
        {"name": "NURDIANA SOPIAN SAHURI", "labor": "20961181"},
    ],
    "Assurance B2B": [
        {"name": "YUSUF SAFARI", "labor": "20971337"},
        {"name": "IKHSAN QOYUM", "labor": "18950127"},
        {"name": "FAJAR GUSTIAN", "labor": "18940109"},
        {"name": "BAYU MAHARDIKA", "labor": "92150121"},
        {"name": "TIA SUTIANA", "labor": "20880008"},
        {"name": "AGENG HAVID H", "labor": "18910274"},
        {"name": "AGUNG APRIANSYAH", "labor": "18960565"},
        {"name": "MUHAMMAD RAMDANI", "labor": "99170353"},
        {"name": "ATH-THARIQ B", "labor": "18990148"},
        {"name": "FREDY RUSDIANA", "labor": "22810002"},
        {"name": "RIDWAN HERDIANA", "labor": "19950028"},
        {"name": "DANI ALFIAN", "labor": "99170347"},
        {"name": "AZIZ FAUZIAN", "labor": "19980255"},
        {"name": "MOCH TAUFIK", "labor": "18910276"},
    ],
    "Provisioning B2B": [
        {"name": "FIKRI FS", "labor": "18990137"},
        {"name": "SAHRUL DARMAWAN", "labor": "19950053"},
        {"name": "SURYADI LESAMA", "labor": "18880014"},
        {"name": "FAISAL NUR AZIZ", "labor": "20940687"},
    ],
    "Maintenance & External": [
        {"name": "SUDRAJAT", "labor": "18740021"},
        {"name": "YANTO HERYANTO", "labor": "19810003"},
        {"name": "DUDUNG ALAMSYAH", "labor": "18960355"},
    ],
}


# ===================== FORM RULES =====================
def tiket_optional(jenis_order: str) -> bool:
    s = (jenis_order or "").lower()
    return ("tangible" in s) or ("ixsa" in s) or ("unspec" in s)


ORDERS_WITH_DATEK_ODP = {
    # Provisioning B2C
    "PSB Indihome",
    "PDA",
    "Survey PT2",
    "Progress PT2",
    # Provisioning B2B
    "PSB DATIN",
    "PSB INDIBIZ",
    "PSB OLO",
    "PSB WIFI",
}


def fields_for_segment(segment: str, jenis_order: str):
    if segment in ASSURANCE_SEGMENTS:
        fields = ["service_no", "tiket_no"]
    else:
        fields = ["service_no", "order_no"]

    if jenis_order in ORDERS_WITH_DATEK_ODP:
        fields.append("datek_odp")

    fields += ["labor1", "labor2", "start_dt", "close_dt", "workzone"]
    return fields


PROMPTS = {
    "service_no": "Isi **service no** (Isi datek ODP kalau tidak ada):",
    "tiket_no": "Isi **tiket no** (kalau tidak ada untuk Tangible/IXSA/Unspec, ketik `-`):",
    "order_no": "Isi **order no**:",
    "datek_odp": "Isi **datek ODP**:",
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
        "pending_payload",
        "last_tech_unit",  # untuk TECH_BACK
    ]:
        context.user_data.pop(k, None)


def start_form(context: ContextTypes.DEFAULT_TYPE, segment: str, jenis_order: str, page: int):
    context.user_data["form_active"] = True
    context.user_data["form_segment"] = segment
    context.user_data["form_order"] = jenis_order
    context.user_data["form_fields"] = fields_for_segment(segment, jenis_order)
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


def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batalkan input", callback_data="CANCEL_FORM")]])


def _allowed_units_for_segment(segment: str):
    # Semua unit teknisi boleh mengerjakan semua jenis pekerjaan
    return list(TECH_UNITS.keys())


def tech_unit_keyboard(target_field: str, segment: str, allow_none: bool = False):
    allowed_units = _allowed_units_for_segment(segment)

    rows = [[InlineKeyboardButton(unit, callback_data=f"TECH_UNIT|{unit}|{target_field}")] for unit in allowed_units]

    if allow_none:
        rows.append([InlineKeyboardButton("➖ Tidak ada teknisi 2", callback_data=f"TECH_NONE|{target_field}")])

    return InlineKeyboardMarkup(rows)


def tech_list_keyboard(unit: str, target_field: str):
    rows = []
    # NOTE: ini bisa panjang, tapi OK untuk sekarang (kalau mau paging nanti kita bikin)
    for i, t in enumerate(TECH_UNITS.get(unit, [])):
        label = f"{t['name']} — {t['labor']}"
        rows.append([InlineKeyboardButton(label, callback_data=f"TECH_PICK|{unit}|{i}|{target_field}")])

    rows.append([InlineKeyboardButton("⬅️ Kembali", callback_data=f"TECH_BACK|{target_field}")])
    return InlineKeyboardMarkup(rows)


# ===================== BOT FLOW =====================
async def ask_next_question(chat_id: int, context: ContextTypes.DEFAULT_TYPE, bot):
    step = context.user_data["form_step"]
    fields = context.user_data["form_fields"]

    if step >= len(fields):
        await finish_form(chat_id, context, bot)
        return

    field = fields[step]

    # labor1 & labor2 pakai menu teknisi
    if field == "labor1":
        await bot.send_message(
            chat_id=chat_id,
            text="Pilih **Unit Teknisi (Teknisi 1)**:",
            reply_markup=tech_unit_keyboard("labor1", context.user_data["form_segment"], allow_none=False),
            parse_mode="Markdown",
        )
        return

    if field == "labor2":
        await bot.send_message(
            chat_id=chat_id,
            text="Pilih **Unit Teknisi (Teknisi 2)**:",
            reply_markup=tech_unit_keyboard("labor2", context.user_data["form_segment"], allow_none=True),
            parse_mode="Markdown",
        )
        return

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
        "man_hours_order": man_hours_for_order(jenis_order),
        "service_no": ans.get("service_no", "").strip(),
        "tiket_no": tiket_no,
        "order_no": order_no,
        "datek_odp": ans.get("datek_odp", "").strip(),
        "labor_code_teknisi_1": ans.get("labor1", "").strip(),
        "labor_code_teknisi_2": ans.get("labor2", "").strip(),
        "nama_teknisi_1": ans.get("labor1_name", "").strip(),
        "nama_teknisi_2": ans.get("labor2_name", "").strip(),
        "start_dt": ans.get("start_dt", "").strip(),
        "close_dt": ans.get("close_dt", "").strip(),
        "workzone": ans.get("workzone", "").strip(),
    }

    context.user_data["pending_payload"] = payload

    summary = (
        "📋 **MOHON KONFIRMASI DATA**\n\n"
        f"**Segment:** {segment}\n"
        f"**Jenis Order:** {jenis_order}\n\n"
        f"service no: {payload['service_no']}\n"
        f"tiket no: {payload['tiket_no']}\n"
        f"order no: {payload['order_no']}\n"
        f"datek ODP: {(payload.get('datek_odp') or '-')}\n"
        f"teknisi 1: {payload.get('nama_teknisi_1','')} ({payload.get('labor_code_teknisi_1','')})\n"
        f"teknisi 2: {(payload.get('nama_teknisi_2') or '-')} ({payload.get('labor_code_teknisi_2') or '-'})\n"
        f"tanggal jam start: {payload['start_dt']}\n"
        f"tanggal jam close: {payload['close_dt']}\n"
        f"workzone: {payload['workzone']}\n\n"
        f"bobot/man-hours order: {payload['man_hours_order']:.2f}\n\n"
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


async def capaian_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    labor_code = ""
    month_key = datetime.now().strftime("%m/%Y")

    if len(args) == 1:
        if _is_month_arg(args[0]):
            month_key = args[0]
        else:
            labor_code = args[0]
    elif len(args) >= 2:
        labor_code = args[0]
        month_key = args[1]

    if not _is_month_arg(month_key):
        await update.message.reply_text("Format bulan salah. Gunakan `MM/YYYY` (contoh `02/2026`).", parse_mode="Markdown")
        return

    if not labor_code:
        await update.message.reply_text(
            "Gunakan format:\n"
            "`/capaian <labor_code> [MM/YYYY]`\n\n"
            "Contoh:\n"
            "`/capaian 20971337`\n"
            "`/capaian 20971337 02/2026`",
            parse_mode="Markdown",
        )
        return

    source_label = "Google Sheet"
    try:
        (total_job, total_mh), detail_rows = get_monthly_summary_from_sheet(labor_code, month_key)
    except Exception:
        # fallback aman ke database lokal jika endpoint sheet belum siap/error
        source_label = "Database Lokal (fallback)"
        (total_job, total_mh), detail_rows = get_monthly_summary(labor_code, month_key)

    if total_job == 0:
        await update.message.reply_text(
            f"Belum ada data untuk labor code *{labor_code}* di bulan *{month_key}*.",
            parse_mode="Markdown",
        )
        return

    lines = [
        "📊 *CAPAIAN MAN HOURS*",
        f"Labor Code: *{labor_code}*",
        f"Bulan: *{month_key}*",
        f"Sumber Data: *{source_label}*",
        f"Total Job: *{total_job}*",
        f"Total Man Hours: *{total_mh:.2f}*",
        "",
        "Rincian per jenis order:",
    ]

    for jenis_order, job_count, mh_sum in detail_rows[:20]:
        lines.append(f"- {jenis_order}: {job_count} job / {mh_sum:.2f} MH")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ===================== BUTTON HANDLER =====================
async def on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # ---- TECH flow ----
    if q.data.startswith("TECH_UNIT|"):
        _, unit, target = q.data.split("|", 2)
        context.user_data["last_tech_unit"] = unit  # untuk tombol back
        await q.edit_message_text(
            f"Pilih **Teknisi** dari unit **{unit}**:",
            reply_markup=tech_list_keyboard(unit, target),
            parse_mode="Markdown",
        )
        return

    if q.data.startswith("TECH_BACK|"):
        _, target = q.data.split("|", 1)
        # balik ke menu unit (yang sesuai segment)
        await q.edit_message_text(
            "Pilih **Unit Teknisi**:",
            reply_markup=tech_unit_keyboard(
                target,
                context.user_data.get("form_segment", ""),
                allow_none=(target == "labor2"),
            ),
            parse_mode="Markdown",
        )
        return

    if q.data.startswith("TECH_PICK|"):
        _, unit, idx, target = q.data.split("|", 3)
        tech = TECH_UNITS[unit][int(idx)]

        context.user_data["form_answers"][target] = tech["labor"]
        context.user_data["form_answers"][f"{target}_name"] = tech["name"]

        context.user_data["form_step"] += 1
        await ask_next_question(q.message.chat_id, context, context.bot)
        return

    if q.data.startswith("TECH_NONE|"):
        _, target = q.data.split("|", 1)
        context.user_data["form_answers"][target] = ""
        context.user_data["form_answers"][f"{target}_name"] = ""
        context.user_data["form_step"] += 1
        await ask_next_question(q.message.chat_id, context, context.bot)
        return

    # ---- CONFIRM SAVE/CANCEL ----
    if q.data == "CONFIRM_SAVE":
        payload = context.user_data.get("pending_payload")
        if not payload:
            await q.edit_message_text("⚠️ Data tidak ditemukan. Ketik /menu untuk ulang.")
            return

        if not GS_WEBAPP_URL:
            await q.edit_message_text("⚠️ GS_WEBAPP_URL belum diset di environment.")
            return

        try:
            r = requests.post(GS_WEBAPP_URL, json=payload, timeout=15)
            if r.status_code == 200:
                save_job_credits(payload)
                recap = (
                    "✅ **Data BERHASIL disimpan ke Google Sheet.**\n\n"
                    "📌 **Ringkasan data:**\n"
                    f"- Segment: {payload.get('segment','')}\n"
                    f"- Jenis Order: {payload.get('jenis_order','')}\n"
                    f"- Service No: {payload.get('service_no','')}\n"
                    f"- Tiket No: {(payload.get('tiket_no') or '-')}\n"
                    f"- Order No: {(payload.get('order_no') or '-')}\n"
                    f"- Datek ODP: {(payload.get('datek_odp') or '-')}\n"
                    f"- Teknisi 1: {payload.get('nama_teknisi_1','')} ({payload.get('labor_code_teknisi_1','')})\n"
                    f"- Teknisi 2: {(payload.get('nama_teknisi_2') or '-')} ({payload.get('labor_code_teknisi_2') or '-'})\n"
                    f"- Start: {payload.get('start_dt','')}\n"
                    f"- Close: {payload.get('close_dt','')}\n"
                    f"- Workzone: {payload.get('workzone','')}\n\n"
                    f"- Bobot/MH Order: {payload.get('man_hours_order', 0):.2f}\n\n"
                    "Ketik /menu untuk input data baru."
                )
                await q.edit_message_text(recap, parse_mode="Markdown")
            else:
                await q.edit_message_text(f"⚠️ Gagal simpan ke Google Sheet (HTTP {r.status_code}).")

        except Exception as e:
            await q.edit_message_text(f"⚠️ Error kirim data: {e}")

        clear_form(context)
        return

    if q.data == "CONFIRM_CANCEL":
        clear_form(context)
        await q.edit_message_text("❌ Input dibatalkan. Ketik /menu untuk mulai ulang.")
        return

    # ---- CANCEL / HOME ----
    if q.data == "CANCEL_FORM":
        clear_form(context)
        await q.edit_message_text("✅ Input dibatalkan. Ketik /menu untuk mulai lagi.")
        return

    if q.data == "HOME":
        clear_form(context)
        await q.edit_message_text(
            "Silakan pilih **Segment**:",
            reply_markup=segment_keyboard(),
            parse_mode="Markdown",
        )
        return

    # ---- SEGMENT paging ----
    if q.data.startswith("SEG|"):
        _, segment, page_str = q.data.split("|", 2)
        page = int(page_str)
        total = len(SEGMENT_ORDERS.get(segment, []))
        max_page = (total - 1) // PAGE_SIZE if total else 0
        text = f"**Segment:** {segment}\nPilih Jenis Order (Hal {page+1}/{max_page+1})"
        await q.edit_message_text(text, reply_markup=orders_keyboard(segment, page), parse_mode="Markdown")
        return

    # ---- ORDER pick ----
    if q.data.startswith("ORD|"):
        _, segment, idx_str, page_str = q.data.split("|", 3)
        idx = int(idx_str)
        page = int(page_str)

        orders = SEGMENT_ORDERS.get(segment, [])
        if not (0 <= idx < len(orders)):
            await q.edit_message_text("Pilihan order tidak valid. Ketik /menu untuk ulang.")
            return

        jenis_order = orders[idx]
        start_form(context, segment, jenis_order, page)

        context.user_data["telegram_user_id"] = update.effective_user.id if update.effective_user else ""

        await q.edit_message_text(
            f"✅ Dipilih:\n"
            f"Segment: {segment}\n"
            f"Jenis Order: {jenis_order}\n\n"
            "Sekarang kita mulai input data satu per satu.\n"
            "Ketik /cancel untuk membatalkan.",
            parse_mode="Markdown",
        )

        await ask_next_question(q.message.chat_id, context, context.bot)
        return


# ===================== TEXT INPUT HANDLER =====================
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not form_active(context):
        await update.message.reply_text("Ketik /menu untuk mulai input pekerjaan, dan ketik /capaian untuk melihat capaian dalam 1 bulan.")
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

    elif field == "tiket_no":
        if text == "-" or text == "":
            if segment in ASSURANCE_SEGMENTS and tiket_optional(jenis_order):
                context.user_data["form_answers"][field] = ""
            else:
                await update.message.reply_text("Tiket no tidak boleh kosong untuk order ini. Isi tiket no.")
                return
        else:
            context.user_data["form_answers"][field] = text

    elif field == "datek_odp":
        if text == "":
            await update.message.reply_text("Datek ODP **wajib diisi** untuk jenis order ini.")
            return
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
            context.user_data["form_step"] = fields.index("close_dt")
            return

    # ----- next step -----
    context.user_data["form_step"] += 1
    await ask_next_question(update.effective_chat.id, context, context.bot)


# ===================== MAIN =====================
def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN belum di-set di environment.")
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("capaian", capaian_cmd))
    app.add_handler(CallbackQueryHandler(on_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    print("✅ Bot sedang berjalan... tekan Ctrl+C untuk berhenti.")
    app.run_polling()


if __name__ == "__main__":
    main()







