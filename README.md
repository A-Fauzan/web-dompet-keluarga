# 💰 Bot Telegram Pencatat Pengeluaran

Bot Telegram untuk mencatat pengeluaran rumah tangga secara mudah dan cepat. Dibuat untuk **Fauzan & Venska**.

---

## ✨ Fitur

- **Multi transaksi** dalam satu pesan — pisahkan dengan koma, titik koma, baris baru, atau kata "dan"
- **Auto kategorisasi** — ketik "beli telur" otomatis masuk kategori Makanan
- **Rekap pengeluaran** berdua lengkap dengan persentase dan progress bar
- **Analisis per kategori** — lihat pengeluaran terbesar di kategori apa
- **History per tanggal** — riwayat 7 hari, 30 hari, bulan ini, atau semua
- **Hapus transaksi** — pilih sendiri mana yang ingin dihapus dari 5 terakhir
- **Database cloud (Turso)** — data aman meski bot di-redeploy

---

## 📋 Cara Pakai

### Catat Pengeluaran
Langsung ketik tanpa perintah apapun:
```
bensin 100rb
```
```
bensin 100rb, ganti oli 75rb, makan 35rb
```
```
beli telur 25rb
listrik 200rb
popok 420rb
```

### Perintah
| Perintah | Fungsi |
|----------|--------|
| `/start` | Registrasi / sapa bot |
| `/rekap` | Rekap pengeluaran berdua + persentase |
| `/analisis` | Breakdown per kategori |
| `/history` | Riwayat pengeluaran per tanggal |
| `/hapus` | Hapus transaksi tertentu |
| `/bantuan` | Panduan lengkap |

### Kategori Otomatis
| Kategori | Contoh Kata Kunci |
|----------|-------------------|
| 🍔 Makanan | makan, telur, bakso, warung, sayur |
| 🚗 Transportasi | bensin, gojek, parkir, servis motor |
| 🏠 Rumah | listrik, wifi, gas, sabun, sewa |
| 👶 Anak | popok, pampers, susu formula |
| 💊 Kesehatan | obat, dokter, apotek, bpjs |
| 👕 Pakaian | baju, sepatu, jaket |
| 📱 Elektronik | pulsa, kuota, netflix, charger |
| 📦 Lain-lain | (selain kategori di atas) |

---

## 🚀 Deployment

Bot di-host di **Railway.app** dan database di **Turso** (SQLite cloud).

### Prasyarat
- Akun [Railway.app](https://railway.app)
- Akun [Turso](https://turso.tech)
- Bot Token dari [@BotFather](https://t.me/BotFather)

### Langkah Deploy
1. Fork/clone repo ini ke GitHub
2. Buat database baru di Turso, catat URL dan Token-nya
3. Connect repo ke Railway → **New Project → Deploy from GitHub**
4. Set environment variables di Railway:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Token dari BotFather |
| `TURSO_URL` | `libsql://nama-db.turso.io` |
| `TURSO_TOKEN` | Token dari Turso dashboard |

5. Railway otomatis deploy — selesai! 🎉

---

## 🗂️ Struktur File

```
├── bot_v4.py          # Kode utama bot
├── requirements.txt   # Dependency Python
├── Procfile           # Perintah start Railway
└── README.md
```

### requirements.txt
```
python-telegram-bot==21.6
libsql-experimental
```

### Procfile
```
worker: python bot_v4.py
```

---

## 🗄️ Struktur Database

**Tabel `pengeluaran`**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INTEGER | Primary key |
| nama | TEXT | fauzan / venska |
| keterangan | TEXT | Deskripsi (misal: bensin) |
| kategori | TEXT | Kategori otomatis |
| jumlah | INTEGER | Nominal (Rupiah) |
| tanggal | TEXT | Format YYYY-MM-DD |

**Tabel `users`**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| telegram_id | INTEGER | ID Telegram pengguna |
| nama | TEXT | Nama terdaftar |

---

## 🔄 Update Fitur

1. Edit `bot_v4.py`
2. Commit & push ke GitHub
3. Railway otomatis redeploy
4. Data di Turso tetap aman ✅

---

*Bot pribadi untuk pencatatan keuangan rumah tangga.*
