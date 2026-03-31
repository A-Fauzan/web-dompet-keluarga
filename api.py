"""
Flask REST API — Dompet Keluarga Fauzan & Venska
Dijalankan di Railway, terhubung ke Turso DB yang sama dengan bot Telegram.
"""

import os
import libsql_experimental as libsql
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import date

app = Flask(__name__)
CORS(app)  # Izinkan akses dari GitHub Pages (cross-origin)

TURSO_URL   = os.environ.get("TURSO_URL")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN")


# ── DATABASE ────────────────────────────────────────────────────────────────────

def get_con():
    return libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)

def init_db():
    """Tambah kolom tipe jika belum ada (backward compatible)."""
    con = get_con()
    # Tabel utama (sudah ada dari bot)
    con.execute("""
        CREATE TABLE IF NOT EXISTS pengeluaran (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nama       TEXT NOT NULL,
            keterangan TEXT NOT NULL,
            kategori   TEXT NOT NULL,
            jumlah     INTEGER NOT NULL,
            tanggal    TEXT NOT NULL
        )
    """)
    # Tambah kolom tipe jika belum ada (tidak merusak data lama)
    try:
        con.execute("ALTER TABLE pengeluaran ADD COLUMN tipe TEXT NOT NULL DEFAULT 'pengeluaran'")
        con.commit()
    except Exception:
        pass  # Kolom sudah ada, tidak apa-apa


# ── ROUTES ──────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "msg": "Dompet Keluarga API berjalan ✅"})


@app.route("/transactions", methods=["GET"])
def get_transactions():
    """
    Ambil transaksi. Parameter opsional:
      ?month=YYYY-MM   → filter bulan tertentu
      ?nama=Fauzan     → filter per orang
    """
    month = request.args.get("month")   # contoh: 2025-04
    nama  = request.args.get("nama")

    con = get_con()
    query = "SELECT id, nama, keterangan, kategori, jumlah, tanggal, COALESCE(tipe,'pengeluaran') as tipe FROM pengeluaran WHERE 1=1"
    params = []

    if month:
        query += " AND tanggal LIKE ?"
        params.append(month + "%")
    if nama:
        query += " AND nama = ?"
        params.append(nama)

    query += " ORDER BY tanggal DESC, id DESC"
    rows = con.execute(query, params).fetchall()

    result = [
        {
            "id":         r[0],
            "nama":       r[1],
            "keterangan": r[2],
            "kategori":   r[3],
            "jumlah":     r[4],
            "tanggal":    r[5],
            "tipe":       r[6],
        }
        for r in rows
    ]
    return jsonify(result)


@app.route("/transactions", methods=["POST"])
def add_transaction():
    """
    Tambah transaksi baru.
    Body JSON: { nama, keterangan, kategori, jumlah, tanggal?, tipe? }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON kosong"}), 400

    nama       = data.get("nama", "").strip()
    keterangan = data.get("keterangan", "").strip()
    kategori   = data.get("kategori", "Lain-lain").strip()
    jumlah     = data.get("jumlah")
    tanggal    = data.get("tanggal") or date.today().isoformat()
    tipe       = data.get("tipe", "pengeluaran")  # 'pengeluaran' atau 'pemasukan'

    if not nama or not keterangan or jumlah is None:
        return jsonify({"error": "Field nama, keterangan, dan jumlah wajib diisi"}), 400

    try:
        jumlah = int(jumlah)
        if jumlah <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Jumlah harus angka positif"}), 400

    con = get_con()
    con.execute(
        "INSERT INTO pengeluaran (nama, keterangan, kategori, jumlah, tanggal, tipe) VALUES (?,?,?,?,?,?)",
        (nama, keterangan, kategori, jumlah, tanggal, tipe)
    )
    con.commit()

    return jsonify({"success": True, "msg": f"Transaksi '{keterangan}' berhasil disimpan"}), 201


@app.route("/transactions/<int:tx_id>", methods=["DELETE"])
def delete_transaction(tx_id):
    """Hapus transaksi berdasarkan ID."""
    con = get_con()
    row = con.execute("SELECT id, keterangan, jumlah FROM pengeluaran WHERE id=?", (tx_id,)).fetchone()
    if not row:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    con.execute("DELETE FROM pengeluaran WHERE id=?", (tx_id,))
    con.commit()
    return jsonify({"success": True, "deleted": {"id": row[0], "keterangan": row[1], "jumlah": row[2]}})


@app.route("/summary", methods=["GET"])
def get_summary():
    """
    Ringkasan per bulan.
    ?month=YYYY-MM
    """
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    con = get_con()
    rows = con.execute(
        "SELECT COALESCE(tipe,'pengeluaran'), SUM(jumlah) FROM pengeluaran WHERE tanggal LIKE ? GROUP BY tipe",
        (month + "%",)
    ).fetchall()
    result = {"pemasukan": 0, "pengeluaran": 0, "month": month}
    for tipe, total in rows:
        result[tipe] = total or 0
    result["saldo"] = result["pemasukan"] - result["pengeluaran"]
    return jsonify(result)


# ── RUN ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
