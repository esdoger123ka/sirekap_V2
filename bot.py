diff --git a/bot.py b/bot.py
index bff87ed0690c65d7f547714e86f71b95e75691d7..b8bc60a2e89dcf8382e77f9e6f5e7ae93386dd58 100644
--- a/bot.py
+++ b/bot.py
@@ -1,45 +1,48 @@
 from __future__ import annotations
 
-import os
-from datetime import datetime
-import requests
+import os
+import re
+import sqlite3
+from datetime import datetime
+import requests
 
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
-PAGE_SIZE = 8
+PAGE_SIZE = 8
+DB_PATH = os.getenv("BOT_DB_PATH", "bot_data.db")
 
 
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
@@ -126,51 +129,277 @@ SEGMENT_ORDERS = {
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
         "Survey PT2",
         "Progress PT2",
         "REPLACEMENT STB",
         "Tiket FFG Indihome",
     ],
 }
 
 SEGMENTS = list(SEGMENT_ORDERS.keys())
 
 ASSURANCE_SEGMENTS = {"Assurance B2B Internal", "Assurance B2B Eksternal", "Assurance B2C"}
-PROVISIONING_SEGMENTS = {"Provisioning B2B", "Provisioning B2B Eksternal", "Provisioning B2C"}
+PROVISIONING_SEGMENTS = {"Provisioning B2B", "Provisioning B2B Eksternal", "Provisioning B2C"}
+
+
+# ===================== BOBOT / MAN HOURS =====================
+# Sumber dari user; jenis order yang tidak terdefinisi dianggap 0.
+ORDER_MAN_HOURS = {
+    # Assurance B2B Eksternal
+    "Aktivasi Cross Connect TDE": 4.0,
+    "Aktivasi/Migrasi/Dismantel DCS": 4.0,
+    "Aktivasi/Migrasi/Dismantel Digiserve": 4.0,
+    "Aktivasi/Migrasi/Dismantel Hypernet": 4.0,
+    "Corrective Akses Tower CENTRATAMA": 4.0,
+    "Corrective Akses Tower Lintasarta": 4.0,
+    "Corrective Akses Tower UMT": 4.0,
+    "Corrective Cross Connect TDE": 4.0,
+    "Corrective CSA": 4.0,
+    "Corrective DCS": 4.0,
+    "Corrective Digiserve": 4.0,
+    "Corrective Hypernet": 4.0,
+    "Corrective MMP": 4.0,
+    "Corrective MyRep": 4.0,
+    "Corrective NuTech": 2.0,
+    "Corrective SNT": 4.0,
+    "Corrective SPBU": 4.0,
+    "Corrective TBG": 4.0,
+    "Corrective Tower POLARIS": 4.0,
+    "Corrective Tower TIS": 4.0,
+    "Inventory SPBU": 4.0,
+    "Preventif MMP": 2.0,
+    "Preventive Akses Tower CENTRATAMA": 2.0,
+    "Preventive Akses Tower Lintasarta": 2.0,
+    "Preventive Akses Tower UMT": 2.0,
+    "Preventive Asianet": 2.67,
+    "Preventive CSA": 2.0,
+    "Preventive NuTech": 2.0,
+    "Preventive SPBU": 4.0,
+    "Preventive TBG": 2.0,
+    "Preventive Tower POLARIS": 2.0,
+    "Preventive Tower TIS": 2.0,
+    "Relokasi DCS": 1.0,
+    "Relokasi Digiserve": 1.0,
+    "Relokasi Hypernet": 1.0,
+    "Corrective Mitratel": 4.0,
+    # Assurance B2B Internal
+    "HSI Indihome Reseller": 2.0,
+    "Tiket Datin Kategori 1": 2.67,
+    "Tiket Datin Kategori 2": 2.67,
+    "Tiket Datin Kategori 3": 2.67,
+    "Tiket HSI Indibiz": 2.0,
+    "Tiket NodeB CNQ (Preventive/Quality)": 4.0,
+    "Tiket NodeB Critical": 6.0,
+    "Tiket NodeB Low": 4.0,
+    "Tiket NodeB Major": 4.0,
+    "Tiket NodeB Minor": 4.0,
+    "Tiket NodeB Premium": 6.0,
+    "Tiket NodeB Premium Preventive": 4.0,
+    "Tiket OLO Datin Gamas": 4.0,
+    "Tiket OLO Datin Non Gamas": 4.0,
+    "Tiket OLO Datin Quality": 4.0,
+    "Tiket OLO SL WDM": 4.0,
+    "Tiket OLO SL WDM Quality": 4.0,
+    "Tiket Pra SQM Gaul HSI": 2.0,
+    "Tiket SIP Trunk": 2.67,
+    "Tiket SQM Datin": 2.67,
+    "Tiket SQM HSI": 2.0,
+    "Tiket WIFI ID": 2.67,
+    "Tiket Wifi Logic": 2.67,
+    "Unspec DATIN": 2.67,
+    "Unspec HSI": 2.0,
+    "Unspec SITE": 2.0,
+    "Unspec WIFI": 2.0,
+    # Assurance B2C
+    "Dismantling DC": 1.0,
+    "Infracare": 2.0,
+    "IXSA FTM": 4.0,
+    "IXSA ODC": 4.0,
+    "IXSA OLT": 2.0,
+    "Lapsung (Laporan Langsung)": 2.0,
+    "SQM Reguler": 2.0,
+    "Tangible ODP": 2.0,
+    "Unspec Reguler": 2.0,
+    "Validasi Tiang": 0.3,
+    "Valins FTM": 4.0,
+    "Valins ODC": 4.0,
+    "Valins Regular": 0.5,
+    # Provisioning B2B
+    "PSB INDIBIZ": 5.3,
+    "PSB OLO": 6.3,
+    "PSB WIFI": 6.3,
+    "Tiket FFG DATIN": 2.0,
+    "Tiket FFG HSI": 2.0,
+    "Tiket FFG WIFI": 2.0,
+    # Provisioning B2B Eksternal
+    "Preventive Fiberisasi": 2.0,
+    "PSB MyRep": 2.0,
+    "PSB Surge": 2.0,
+    # Provisioning B2C
+    "DISMANTLING ONT": 0.67,
+    "DISMANTLING PLC": 0.67,
+    "DISMANTLING STB": 0.67,
+    "DISMANTLING WIFI EXTENDER": 0.67,
+    "DISMANTLING FWA": 0.67,
+    "PDA": 5.3,
+    "PSB Indihome": 5.3,
+    "REPLACEMENT ONT Premium/Dual Band": 1.33,
+    "REPLACEMENT STB": 1.33,
+    "Tiket FFG Indihome": 2.0,
+    "Survey PT2": 1.5,
+    "Progress PT2": 2.0,
+}
+
+
+def man_hours_for_order(jenis_order: str) -> float:
+    return float(ORDER_MAN_HOURS.get(jenis_order, 0.0))
+
+
+def month_key_from_dt(dt_str: str) -> str:
+    dt = parse_dt(dt_str or "")
+    if not dt:
+        dt = datetime.now()
+    return dt.strftime("%m/%Y")
+
+
+def get_conn():
+    return sqlite3.connect(DB_PATH)
+
+
+def init_db():
+    with get_conn() as conn:
+        conn.execute(
+            """
+            CREATE TABLE IF NOT EXISTS job_credits (
+                id INTEGER PRIMARY KEY AUTOINCREMENT,
+                telegram_user_id TEXT,
+                labor_code TEXT NOT NULL,
+                teknisi_name TEXT,
+                segment TEXT,
+                jenis_order TEXT,
+                close_dt TEXT,
+                month_key TEXT,
+                man_hours REAL NOT NULL,
+                timestamp_input TEXT
+            )
+            """
+        )
+        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_credits_labor_month ON job_credits (labor_code, month_key)")
+        conn.commit()
+
+
+def save_job_credits(payload: dict):
+    month_key = month_key_from_dt(payload.get("close_dt", ""))
+    mh = float(payload.get("man_hours_order", 0.0) or 0.0)
+    rows = []
+
+    if payload.get("labor_code_teknisi_1"):
+        rows.append(
+            (
+                str(payload.get("telegram_user_id", "")),
+                payload.get("labor_code_teknisi_1", ""),
+                payload.get("nama_teknisi_1", ""),
+                payload.get("segment", ""),
+                payload.get("jenis_order", ""),
+                payload.get("close_dt", ""),
+                month_key,
+                mh,
+                payload.get("timestamp_input", ""),
+            )
+        )
+
+    if payload.get("labor_code_teknisi_2"):
+        rows.append(
+            (
+                str(payload.get("telegram_user_id", "")),
+                payload.get("labor_code_teknisi_2", ""),
+                payload.get("nama_teknisi_2", ""),
+                payload.get("segment", ""),
+                payload.get("jenis_order", ""),
+                payload.get("close_dt", ""),
+                month_key,
+                mh,
+                payload.get("timestamp_input", ""),
+            )
+        )
+
+    if not rows:
+        return
+
+    with get_conn() as conn:
+        conn.executemany(
+            """
+            INSERT INTO job_credits (
+                telegram_user_id, labor_code, teknisi_name, segment, jenis_order,
+                close_dt, month_key, man_hours, timestamp_input
+            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
+            """,
+            rows,
+        )
+        conn.commit()
+
+
+def _is_month_arg(text: str) -> bool:
+    return bool(re.fullmatch(r"(0[1-9]|1[0-2])/\d{4}", text or ""))
+
+
+def get_monthly_summary(labor_code: str, month_key: str):
+    with get_conn() as conn:
+        total_row = conn.execute(
+            """
+            SELECT COUNT(*), COALESCE(SUM(man_hours), 0)
+            FROM job_credits
+            WHERE labor_code = ? AND month_key = ?
+            """,
+            (labor_code, month_key),
+        ).fetchone()
+
+        detail_rows = conn.execute(
+            """
+            SELECT jenis_order, COUNT(*) AS total_job, COALESCE(SUM(man_hours), 0) AS total_mh
+            FROM job_credits
+            WHERE labor_code = ? AND month_key = ?
+            GROUP BY jenis_order
+            ORDER BY total_mh DESC, total_job DESC, jenis_order ASC
+            """,
+            (labor_code, month_key),
+        ).fetchall()
+
+    return total_row, detail_rows
 
 
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
         {"name": "FIRMAN FUJI KHOMIRUN", "labor": "POJ3BDB2_016"},
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
@@ -429,113 +658,169 @@ async def ask_next_question(chat_id: int, context: ContextTypes.DEFAULT_TYPE, bo
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
 
-    payload = {
-        "timestamp_input": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
-        "telegram_user_id": str(user_id),
-        "segment": segment,
-        "jenis_order": jenis_order,
-        "service_no": ans.get("service_no", "").strip(),
+    payload = {
+        "timestamp_input": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
+        "telegram_user_id": str(user_id),
+        "segment": segment,
+        "jenis_order": jenis_order,
+        "man_hours_order": man_hours_for_order(jenis_order),
+        "service_no": ans.get("service_no", "").strip(),
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
-        f"workzone: {payload['workzone']}\n\n"
-        "Apakah data ini sudah benar?"
-    )
+        f"workzone: {payload['workzone']}\n\n"
+        f"bobot/man-hours order: {payload['man_hours_order']:.2f}\n\n"
+        "Apakah data ini sudah benar?"
+    )
 
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
 
 
-async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
+async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
     if form_active(context):
         clear_form(context)
         await update.message.reply_text("✅ Input dibatalkan. Ketik /menu untuk mulai lagi.")
     else:
-        await update.message.reply_text("Tidak ada input aktif. Ketik /menu untuk mulai.")
+        await update.message.reply_text("Tidak ada input aktif. Ketik /menu untuk mulai.")
+
+
+async def capaian_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
+    args = context.args or []
+    labor_code = ""
+    month_key = datetime.now().strftime("%m/%Y")
+
+    if len(args) == 1:
+        if _is_month_arg(args[0]):
+            month_key = args[0]
+        else:
+            labor_code = args[0]
+    elif len(args) >= 2:
+        labor_code = args[0]
+        month_key = args[1]
+
+    if not _is_month_arg(month_key):
+        await update.message.reply_text("Format bulan salah. Gunakan `MM/YYYY` (contoh `02/2026`).", parse_mode="Markdown")
+        return
+
+    if not labor_code:
+        await update.message.reply_text(
+            "Gunakan format:\n"
+            "`/capaian <labor_code> [MM/YYYY]`\n\n"
+            "Contoh:\n"
+            "`/capaian 20971337`\n"
+            "`/capaian 20971337 02/2026`",
+            parse_mode="Markdown",
+        )
+        return
+
+    (total_job, total_mh), detail_rows = get_monthly_summary(labor_code, month_key)
+
+    if total_job == 0:
+        await update.message.reply_text(
+            f"Belum ada data untuk labor code *{labor_code}* di bulan *{month_key}*.",
+            parse_mode="Markdown",
+        )
+        return
+
+    lines = [
+        "📊 *CAPAIAN MAN HOURS*",
+        f"Labor Code: *{labor_code}*",
+        f"Bulan: *{month_key}*",
+        f"Total Job: *{total_job}*",
+        f"Total Man Hours: *{total_mh:.2f}*",
+        "",
+        "Rincian per jenis order:",
+    ]
+
+    for jenis_order, job_count, mh_sum in detail_rows[:20]:
+        lines.append(f"- {jenis_order}: {job_count} job / {mh_sum:.2f} MH")
+
+    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
 
 
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
@@ -555,68 +840,70 @@ async def on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
 
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
-            r = requests.post(GS_WEBAPP_URL, json=payload, timeout=15)
-            if r.status_code == 200:
-                recap = (
-                    "✅ **Data BERHASIL disimpan ke Google Sheet.**\n\n"
-                    "📌 **Ringkasan data:**\n"
+            r = requests.post(GS_WEBAPP_URL, json=payload, timeout=15)
+            if r.status_code == 200:
+                save_job_credits(payload)
+                recap = (
+                    "✅ **Data BERHASIL disimpan ke Google Sheet.**\n\n"
+                    "📌 **Ringkasan data:**\n"
                     f"- Segment: {payload.get('segment','')}\n"
                     f"- Jenis Order: {payload.get('jenis_order','')}\n"
                     f"- Service No: {payload.get('service_no','')}\n"
                     f"- Tiket No: {(payload.get('tiket_no') or '-')}\n"
                     f"- Order No: {(payload.get('order_no') or '-')}\n"
                     f"- Datek ODP: {(payload.get('datek_odp') or '-')}\n"
                     f"- Teknisi 1: {payload.get('nama_teknisi_1','')} ({payload.get('labor_code_teknisi_1','')})\n"
                     f"- Teknisi 2: {(payload.get('nama_teknisi_2') or '-')} ({payload.get('labor_code_teknisi_2') or '-'})\n"
                     f"- Start: {payload.get('start_dt','')}\n"
-                    f"- Close: {payload.get('close_dt','')}\n"
-                    f"- Workzone: {payload.get('workzone','')}\n\n"
-                    "Ketik /menu untuk input data baru."
-                )
+                    f"- Close: {payload.get('close_dt','')}\n"
+                    f"- Workzone: {payload.get('workzone','')}\n\n"
+                    f"- Bobot/MH Order: {payload.get('man_hours_order', 0):.2f}\n\n"
+                    "Ketik /menu untuk input data baru."
+                )
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
@@ -703,44 +990,46 @@ async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
-def main():
-    if not TOKEN:
-        raise RuntimeError("BOT_TOKEN belum di-set di environment.")
-    app = Application.builder().token(TOKEN).build()
+def main():
+    if not TOKEN:
+        raise RuntimeError("BOT_TOKEN belum di-set di environment.")
+    init_db()
+    app = Application.builder().token(TOKEN).build()
 
     app.add_handler(CommandHandler("start", start_cmd))
-    app.add_handler(CommandHandler("menu", menu_cmd))
-    app.add_handler(CommandHandler("cancel", cancel_cmd))
+    app.add_handler(CommandHandler("menu", menu_cmd))
+    app.add_handler(CommandHandler("cancel", cancel_cmd))
+    app.add_handler(CommandHandler("capaian", capaian_cmd))
 
     app.add_handler(CallbackQueryHandler(on_click))
     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
 
     print("✅ Bot sedang berjalan... tekan Ctrl+C untuk berhenti.")
     app.run_polling()
 
 
 if __name__ == "__main__":
     main()
 
