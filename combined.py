"""
combined.py — Menjalankan Flask API + Telegram Bot dalam satu proses
Flask berjalan di main thread (agar Railway health check terpenuhi)
Bot Telegram berjalan di background thread dengan auto-retry
"""

import threading
import asyncio
import time
import os
from api import app, init_db


def run_bot():
    """Jalankan bot di background thread. Auto-retry jika 409 Conflict."""
    from bot_v4 import main as bot_main
    print("[BOT] Telegram bot dimulai...")

    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            bot_main()
        except Exception as e:
            err = str(e)
            if "Conflict" in err or "409" in err:
                print("[BOT] 409 Conflict — instance lain masih aktif. Retry dalam 15 detik...")
                time.sleep(15)
            else:
                print(f"[BOT] Error: {e}. Retry dalam 5 detik...")
                time.sleep(5)
        finally:
            try:
                loop.close()
            except Exception:
                pass


if __name__ == "__main__":
    # 1. Inisialisasi database
    init_db()

    # 2. Jalankan bot di background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("[BOT] Thread bot dimulai.")

    # 3. Jalankan Flask di main thread (Railway health check butuh ini)
    from waitress import serve
    port = int(os.environ.get("PORT", 8080))
    print(f"[API] Flask berjalan di port {port}...")
    serve(app, host="0.0.0.0", port=port)
