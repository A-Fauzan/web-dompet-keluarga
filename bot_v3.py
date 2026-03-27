
"""
Bot Telegram Pencatat Pengeluaran - Fauzan & Venska
v3.0 — Multi transaksi, auto kategori, history per tanggal
"""

import sqlite3
import re
import logging
from datetime import datetime, date, timedelta
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import nest_asyncio # Import nest_asyncio
import asyncio # Import asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# ── CONFIG ─────────────────────────────────────────────────────────────────────
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")

USERS = {
    "@ahmdfauzn": 0,
    "@merhabavenska": 0,
}
# ───────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
DB = "pengeluaran.db"


# ── AUTO KATEGORISASI ──────────────────────────────────────────────────────────
KATEGORI_KEYWORDS = {
    "Makanan": [
        "makan", "minum", "telur", "beras", "sayur", "sayuran", "buah", "snack",
        "cemilan", "kopi", "teh", "warung", "resto", "restoran", "nasi", "lauk",
        "ayam", "ikan", "daging", "tempe", "tahu", "indomie", "mie", "roti",
        "susu", "jajan", "bakso", "soto", "warteg", "catering", "grocery",
        "belanja dapur", "bumbu", "minyak goreng", "gula", "garam", "tepung",
        "kecap", "saus", "minuman", "jus", "es", "kue", "pizza", "burger",
        "gorengan", "bubur", "sarapan", "makan siang", "makan malam", "makan pagi",
        "beli telur", "beli sayur", "beli buah"
    ],
    "Transportasi": [
        "bensin", "bbm", "pertalite", "pertamax", "solar", "oli", "ganti oli",
        "servis", "bengkel", "ban", "parkir", "tol", "grab", "gojek", "ojek",
        "taksi", "bus", "angkot", "kereta", "krl", "mrt", "busway", "transjakarta",
        "ojol", "motor", "mobil", "sparepart", "spare part", "aki", "tune up",
        "cuci motor", "cuci mobil", "derek", "tilang"
    ],
    "Rumah": [
        "listrik", "pln", "air", "pdam", "pam", "wifi", "internet", "telkom",
        "sewa", "kos", "kontrakan", "iuran", "arisan", "sampah", "gas", "lpg",
        "furnitur", "perabot", "sofa", "lemari", "kasur", "bantal", "sprei",
        "sabun", "deterjen", "pembersih", "pel", "sapu", "renovasi", "cat",
        "genteng", "keramik", "pipa", "kran", "lampu", "barang rumah"
    ],
    "Anak": [
        "popok", "pampers", "susu formula", "mpasi", "mainan",
        "sekolah", "spp", "uang jajan", "buku pelajaran", "alat tulis",
        "seragam", "sepatu sekolah", "tas sekolah", "les", "kursus",
        "vitamin anak", "imunisasi", "baju anak", "celana anak", "perlengkapan bayi"
    ],
    "Kesehatan": [
        "obat", "dokter", "apotek", "apotik", "rumah sakit", "rs", "klinik",
        "puskesmas", "vitamin", "suplemen", "cek darah", "laboratorium",
        "konsultasi", "bpjs", "rawat", "periksa", "masker", "hansaplast"
    ],
    "Pakaian": [
        "baju", "celana", "kaos", "kemeja", "dress", "rok", "jilbab", "hijab",
        "sepatu", "sandal", "tas", "dompet", "ikat pinggang", "topi",
        "pakaian", "beli baju", "outfit", "jaket", "sweater", "gamis"
    ],
    "Elektronik": [
        "pulsa", "paket data", "token listrik", "kuota", "netflix", "spotify",
        "youtube premium", "aplikasi", "charger", "kabel", "earphone",
        "handphone", "hp", "laptop", "gadget", "elektronik"
    ],
}

KATEGORI_EMOJI = {
    "Makanan": "🍔 Makanan",
    "Transportasi": "🚗 Transportasi",
    "Rumah": "🏠 Rumah",
    "Anak": "👶 Anak",
    "Kesehatan": "💊 Kesehatan",
    "Pakaian": "👕 Pakaian",
    "Elektronik": "📱 Elektronik",
    "Lain-lain": "📦 Lain-lain",
}

def auto_kategori(keterangan):
    ket_lower = keterangan.lower()
    for kategori, keywords in KATEGORI_KEYWORDS.items():
        for kw in keywords:
            if kw in ket_lower:
                return kategori
    return "Lain-lain"


# ── DATABASE ────────────────────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS pengeluaran (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nama       TEXT NOT NULL,
                keterangan TEXT NOT NULL,
                kategori   TEXT NOT NULL,
                jumlah     INTEGER NOT NULL,
                tanggal    TEXT NOT NULL
            )
        """
        )
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                nama        TEXT NOT NULL
            )
        """
        )

def get_nama(telegram_id):
    with sqlite3.connect(DB) as con:
        row = con.execute("SELECT nama FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    return row[0] if row else None

def register_user(telegram_id, nama):
    with sqlite3.connect(DB) as con:
        con.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (telegram_id, nama))

def simpan(nama, keterangan, kategori, jumlah):
    today = date.today().isoformat()
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO pengeluaran (nama,keterangan,kategori,jumlah,tanggal) VALUES (?,?,?,?,?)",
            (nama, keterangan, kategori, jumlah, today)
        )

def get_recent_expenses(nama, limit=5):
    with sqlite3.connect(DB) as con:
        rows = con.execute(
            "SELECT id, keterangan, jumlah, tanggal FROM pengeluaran WHERE nama=? ORDER BY id DESC LIMIT ?",
            (nama, limit)
        ).fetchall()
    return rows

def delete_expense_by_id(expense_id):
    with sqlite3.connect(DB) as con:
        row = con.execute(
            "SELECT id, keterangan, jumlah FROM pengeluaran WHERE id=?",
            (expense_id,)
        ).fetchone()
        if row:
            con.execute("DELETE FROM pengeluaran WHERE id=?", (expense_id,))
            return {"keterangan": row[1], "jumlah": row[2]}
    return None

def query_rows(where_clause, params):
    with sqlite3.connect(DB) as con:
        return con.execute(
            "SELECT nama, keterangan, kategori, jumlah, tanggal FROM pengeluaran " + where_clause,
            params
        ).fetchall()


# ── PARSER ─────────────────────────────────────────────────────────────────────
def parse_angka(text):
    text = text.strip()
    m = re.search(r'(\d+(?:[,\.]\d+)?)\s*(jt|juta|rb|ribu|k)\b', text, re.IGNORECASE)
    if m:
        angka = float(m.group(1).replace(",", "."))
        s = m.group(2).lower()
        if s in ("jt", "juta"):      return int(angka * 1_000_000)
        if s in ("rb", "ribu", "k"): return int(angka * 1_000)
    m2 = re.search(r'\b(\d{3,})\b', text)
    if m2:
        return int(m2.group(1))
    return None

def parse_satu(text):
    jumlah = parse_angka(text)
    if jumlah is None:
        return None
    ket = re.sub(
        r'\b\d+(?:[,\.]\d+)?\s*(?:jt|juta|rb|ribu|k)?\b', '', text,
        flags=re.IGNORECASE
    ).strip(" -, ")
    ket = re.sub(r'\s+', ' ', ket).strip()
    if not ket:
        ket = "Lain-lain"
    return ket.capitalize(), jumlah

def parse_multi(text):
    parts = re.split(r'[\n,;]|\bdan\b', text, flags=re.IGNORECASE)
    hasil = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        parsed = parse_satu(p)
        if parsed:
            hasil.append(parsed)
    return hasil


# ── FORMAT ──────────────────────────────────────────────────────────────────────
def fmt_rp(n):
    return "Rp " + "{:,}".format(n).replace(",", ".")

def bar(persen, panjang=10):
    filled = round(persen / 100 * panjang)
    return "=" * filled + "-" * (panjang - filled)

def fmt_rekap(result):
    label = result["label"]
    data  = result["data"]
    total = result["total"]

    if not data:
        return "Belum ada pengeluaran untuk *" + label + "*."

    lines = ["📊 *Rekap Pengeluaran — " + label + "*\n"]
    for nama, info in sorted(data.items()):
        persen = (info["total"] / total * 100) if total else 0
        # Removed user-specific emojis as per instruction
        lines.append("*" + nama.capitalize() + "* — " + fmt_rp(info["total"]) + " (" + "{:.1f}".format(persen) + "%)")
        lines.append("`[" + bar(persen) + "]` " + "{:.1f}".format(persen) + "%")
        for ket, jml, _ in sorted(info["detail"], key=lambda x: x[1], reverse=True):
            lines.append("  • " + ket + ": " + fmt_rp(jml))
        lines.append("")

    lines.append("\n*💰 Total Bersama: " + fmt_rp(total) + "*")
    return "\n".join(lines)

def fmt_analisis(rows, label):
    if not rows:
        return "Belum ada data untuk *" + label + "*."

    kat_data = {}
    total = 0
    for nama, ket, kat, jml, tgl in rows:
        if kat not in kat_data:
            kat_data[kat] = {"total": 0, "items": []}
        kat_data[kat]["total"] += jml
        kat_data[kat]["items"].append((ket, jml, nama))
        total += jml

    lines = ["🔍 *Analisis per Kategori — " + label + "*\n"]
    for kat, info in sorted(kat_data.items(), key=lambda x: x[1]["total"], reverse=True):
        persen = info["total"] / total * 100 if total else 0
        lines.append(f"*{KATEGORI_EMOJI.get(kat, '📦 Lain-lain')}* {fmt_rp(info['total'])} ({persen:.1f}%) -- `[{bar(persen)}]`")
        for ket, jml, nm in sorted(info["items"], key=lambda x: x[1], reverse=True):
            pemilik = "Fauzan" if nm.lower() == "fauzan" else "Venska"
            lines.append("  (" + pemilik + ") " + ket + ": " + fmt_rp(jml))
        lines.append("")

    lines.append("\n*💰 Total: " + fmt_rp(total) + "*")
    return "\n".join(lines)

def fmt_history(rows, label):
    if not rows:
        return "Belum ada data untuk *" + label + "*."

    by_date = {}
    for nama, ket, kat, jml, tgl in rows:
        if tgl not in by_date:
            by_date[tgl] = []
        by_date[tgl].append((nama, ket, kat, jml))

    total = sum(r[3] for r in rows)
    lines = ["📅 *History Pengeluaran — " + label + "*\n"]

    for tgl in sorted(by_date.keys(), reverse=True):
        items = by_date[tgl]
        subtotal = sum(i[3] for i in items)
        dt = datetime.strptime(tgl, "%Y-%m-%d")
        lines.append("🗓️ *" + dt.strftime("%d %b %Y") + "* — " + fmt_rp(subtotal))
        for nm, ket, kat, jml in items:
            pemilik = "Fauzan" if nm.lower() == "fauzan" else "Venska"
            lines.append("  " + KATEGORI_EMOJI.get(kat, '📦 Lain-lain') + " " + ket + " (" + pemilik + "): " + fmt_rp(jml))
        lines.append("")

    lines.append("\n*💰 Total: " + fmt_rp(total) + "*")
    return "\n".join(lines)


def _proses_rekap(rows, label):
    data = {} # type: dict[str, dict[str, any]]
    for nama, ket, kat, jumlah, tanggal in rows:
        if nama not in data:
            data[nama] = {"total": 0, "detail": []}
        data[nama]["total"] += jumlah
        data[nama]["detail"].append((ket, jumlah, tanggal))
    total_all = sum(v["total"] for v in data.values())
    return {"label": label, "data": data, "total": total_all}

def rekap_bulan(bulan=None):
    if bulan is None:
        bulan = date.today().strftime("%Y-%m")
    rows = query_rows("WHERE tanggal LIKE ?", (bulan + "%",))
    return _proses_rekap(rows, "Bulan " + bulan)

def rekap_hari_ini():
    today = date.today().isoformat()
    rows = query_rows("WHERE tanggal=?", (today,))
    return _proses_rekap(rows, "Hari Ini (" + today + ")")

def rekap_semua():
    rows = query_rows("", ())
    return _proses_rekap(rows, "Semua Waktu")


# ── HANDLERS ────────────────────────────────────────────────────────────────────
async def start(update, ctx):
    nama = get_nama(update.effective_user.id)
    if nama:
        await update.message.reply_text(
            "👋 Halo *" + nama.capitalize() + "*! Bot pengeluaran siap.\n\n"
            "Catat langsung, contoh:\n"
            "`bensin 100rb`\n"
            "`bensin 100rb, ganti oli 75rb, makan 35rb`\n"
            "`beli telur 25rb` (otomatis -> Makanan)\n\n"
            "/rekap /analisis /history /hapus /bantuan",
            parse_mode="Markdown"
        )
    else:
        kb = [[
            InlineKeyboardButton("Fauzan", callback_data="daftar_fauzan"),
            InlineKeyboardButton("Venska", callback_data="daftar_venska"),
        ]]
        await update.message.reply_text(
            "Selamat datang! Kamu siapa?",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def callback_daftar(update, ctx):
    query = update.callback_query
    await query.answer()
    nama = query.data.replace("daftar_", "")
    register_user(query.from_user.id, nama)
    await query.edit_message_text(
        "✅ Terdaftar sebagai *" + nama.capitalize() + "*!\n\n"
        "Langsung catat pengeluaran:\n"
        "`bensin 100rb, ganti oli 75rb`",
        parse_mode="Markdown"
    )

async def cmd_rekap(update, ctx):
    kb = [[
        InlineKeyboardButton("Bulan Ini",   callback_data="rekap_bulan"),
        InlineKeyboardButton("Hari Ini",    callback_data="rekap_hari"),
    ],[
        InlineKeyboardButton("Semua Waktu", callback_data="rekap_semua"),
    ]]
    await update.message.reply_text("Pilih periode rekap:", reply_markup=InlineKeyboardMarkup(kb))

async def callback_rekap(update, ctx):
    query = update.callback_query
    await query.answer()
    if query.data == "rekap_bulan":
        result = rekap_bulan()
    elif query.data == "rekap_hari":
        result = rekap_hari_ini()
    else:
        result = rekap_semua()
    await query.edit_message_text(fmt_rekap(result), parse_mode="Markdown")

async def cmd_analisis(update, ctx):
    kb = [[
        InlineKeyboardButton("Bulan Ini",   callback_data="analisis_bulan"),
        InlineKeyboardButton("Hari Ini",    callback_data="analisis_hari"),
    ],[
        InlineKeyboardButton("Semua Waktu", callback_data="analisis_semua"),
    ]]
    await update.message.reply_text("Pilih periode analisis:", reply_markup=InlineKeyboardMarkup(kb))

async def callback_analisis(update, ctx):
    query = update.callback_query
    await query.answer()
    if query.data == "analisis_bulan":
        bulan = date.today().strftime("%Y-%m")
        rows = query_rows("WHERE tanggal LIKE ?", (bulan + "%",))
        label = "Bulan " + bulan
    elif query.data == "analisis_hari":
        today = date.today().isoformat()
        rows = query_rows("WHERE tanggal=?", (today,))
        label = "Hari Ini (" + today + ")"
    else:
        rows = query_rows("", ())
        label = "Semua Waktu"
    await query.edit_message_text(fmt_analisis(rows, label), parse_mode="Markdown")

async def cmd_history(update, ctx):
    kb = [[
        InlineKeyboardButton("7 Hari Terakhir",  callback_data="history_7"),
        InlineKeyboardButton("30 Hari Terakhir", callback_data="history_30"),
    ],[
        InlineKeyboardButton("Bulan Ini",        callback_data="history_bulan"),
        InlineKeyboardButton("Semua",            callback_data="history_semua"),
    ]]
    await update.message.reply_text("Pilih rentang history:", reply_markup=InlineKeyboardMarkup(kb))

async def callback_history(update, ctx):
    query = update.callback_query
    await query.answer()
    key = query.data

    if key == "history_7":
        since = (date.today() - timedelta(days=7)).isoformat()
        rows = query_rows("WHERE tanggal >= ? ORDER BY tanggal DESC", (since,))
        label = "7 Hari Terakhir"
    elif key == "history_30":
        since = (date.today() - timedelta(days=30)).isoformat()
        rows = query_rows("WHERE tanggal >= ? ORDER BY tanggal DESC", (since,))
        label = "30 Hari Terakhir"
    elif key == "history_bulan":
        bulan = date.today().strftime("%Y-%m")
        rows = query_rows("WHERE tanggal LIKE ? ORDER BY tanggal DESC", (bulan + "%",))
        label = "Bulan " + bulan
    else:
        rows = query_rows("ORDER BY tanggal DESC", ())
        label = "Semua Waktu"

    teks = fmt_history(rows, label)
    if len(teks) > 4000:
        teks = teks[:4000] + "\n\n_...terlalu panjang. Coba filter periode lebih pendek._"
    await query.edit_message_text(teks, parse_mode="Markdown")

async def cmd_hapus(update, ctx):
    nama = get_nama(update.effective_user.id)
    if not nama:
        await update.message.reply_text("Kamu belum terdaftar. Ketik /start")
        return

    recent_expenses = get_recent_expenses(nama, limit=5) # Get last 5 expenses

    if not recent_expenses:
        await update.message.reply_text("Tidak ada pengeluaran terbaru yang bisa dihapus.")
        return

    keyboard = []
    for exp_id, ket, jml, tgl in recent_expenses:
        # Format date for display if needed, e.g., tgl_formatted = datetime.strptime(tgl, '%Y-%m-%d').strftime('%d %b')
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {ket} ({fmt_rp(jml)})",
                callback_data=f"delete_item_{exp_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("❌ Batalkan", callback_data="delete_cancel")])

    await update.message.reply_text(
        "Pilih pengeluaran yang ingin dihapus:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def callback_delete_item(update, ctx):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "delete_cancel":
        await query.edit_message_text("❌ Penghapusan dibatalkan.")
        return

    expense_id = int(data.replace("delete_item_", ""))
    item = delete_expense_by_id(expense_id)

    if item:
        await query.edit_message_text(
            f"🗑️ Dihapus: *{item['keterangan']}* ({fmt_rp(item['jumlah'])})",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("❌ Gagal menghapus atau item tidak ditemukan.")


async def cmd_bantuan(update, ctx):
    await update.message.reply_text(
        "❓ *Panduan Bot Pengeluaran v3*\n\n"
        "*Catat — langsung ketik (bisa multi sekaligus):*\n"
        "  `bensin 100rb`\n"
        "  `bensin 100rb, ganti oli 75rb, makan 35rb`\n"
        "  `beli telur 25rb` (otomatis Makanan)\n"
        "  `listrik 200rb` (otomatis Rumah)\n\n"
        "*Pemisah multi transaksi:*\n"
        "  Koma, titik koma, baris baru, atau 'dan'\n\n"
        "*Kategori otomatis:*\n"
        "  " + KATEGORI_EMOJI["Makanan"] + ", " + KATEGORI_EMOJI["Transportasi"] + ", " + KATEGORI_EMOJI["Rumah"] + "\n"
        "  " + KATEGORI_EMOJI["Anak"] + ", " + KATEGORI_EMOJI["Kesehatan"] + ", " + KATEGORI_EMOJI["Pakaian"] + "\n"
        "  " + KATEGORI_EMOJI["Elektronik"] + ", " + KATEGORI_EMOJI["Lain-lain"] + "\n\n"
        "*Perintah:*\n"
        "  /rekap — rekap berdua + persentase\n"
        "  /analisis — breakdown per kategori\n"
        "  /history — riwayat per tanggal\n"
        "  /hapus — hapus entri terakhirmu (sekarang bisa pilih!)\n"
        "  /bantuan — panduan ini",
        parse_mode="Markdown"
    )

async def pesan_masuk(update, ctx):
    nama = get_nama(update.effective_user.id)
    if not nama:
        await update.message.reply_text("Kamu belum terdaftar. Ketik /start dulu ya!")
        return

    text = update.message.text
    transaksi = parse_multi(text)

    if not transaksi:
        await update.message.reply_text(
            "Format tidak dikenali.\n"
            "Contoh: `bensin 100rb` atau `makan 35rb, bensin 100rb`",
            parse_mode="Markdown"
        )
        return

    lines = ["✅ *" + nama.capitalize() + "* mencatat:\n"]
    total = 0

    for ket, jml in transaksi:
        kat = auto_kategori(ket)
        simpan(nama, ket, kat, jml)
        lines.append("  " + KATEGORI_EMOJI.get(kat, '📦 Lain-lain') + " " + ket + ": " + fmt_rp(jml))
        total += jml

    if len(transaksi) > 1:
        lines.append("\n  Subtotal: *" + fmt_rp(total) + "*")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── MAIN ────────────────────────────────────────────────────────────────────────
# Global variable to hold the application instance
app = None

async def main_async(): # Renamed to main_async to avoid conflict with `main` in `if __name__ == "__main__"`
    global app

    # If an app is already running, shut it down gracefully.
    if app is not None and app.running:
        print("Stopping existing bot instance gracefully...")
        try:
            await app.stop() # Await the stop operation
            print("Previous bot instance stopped.")
        except Exception as e:
            print(f"Error stopping previous bot instance: {e}. Attempting to proceed.")

    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("rekap",    cmd_rekap))
    app.add_handler(CommandHandler("analisis", cmd_analisis))
    app.add_handler(CommandHandler("history",  cmd_history))
    app.add_handler(CommandHandler("hapus",    cmd_hapus))
    app.add_handler(CommandHandler("bantuan",  cmd_bantuan))

    app.add_handler(CallbackQueryHandler(callback_daftar,   pattern=r"^daftar_"))
    app.add_handler(CallbackQueryHandler(callback_rekap,    pattern=r"^rekap_"))
    app.add_handler(CallbackQueryHandler(callback_analisis, pattern=r"^analisis_"))
    app.add_handler(CallbackQueryHandler(callback_history,  pattern=r"^history_"))
    app.add_handler(CallbackQueryHandler(callback_delete_item, pattern=r"^delete_item_|^delete_cancel"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pesan_masuk))

    print("Bot v3 berjalan...")
    await app.run_polling() # Await run_polling

if __name__ == "__main__":
    # Ensure nest_asyncio is applied before running asyncio.run
    nest_asyncio.apply()
    asyncio.run(main_async())
