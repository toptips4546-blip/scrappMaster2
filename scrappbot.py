import sqlite3
import secrets
import asyncio
import requests
import threading
import re
import concurrent.futures
from datetime import datetime
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8270940304:AAGYSQKtrvQ7hupcJ1ybGWzCBJi7TMW-KbI"
CANAL_BINS_ID = -1003659562473
OWNER_ID = 8381780421

BINCODES_API_KEY = ""

LINK_BOT = "https://t.me/AAMasterCheck_bot"
LINK_PROGRAMADOR = "https://t.me/thekingapk1"
LINK_SELLER_OWNER = "https://t.me/Tania90o"
LINK_SELLER_1 = "https://t.me/Pa0_laa"
LINK_SELLER_2 = "https://t.me/cyberdarcks"

VIDEO_FILE_ID = "BAACAgEAAxkBAAFVc9tqwWk7jU9xHSXSmob6E18h5W4YJgACwwkAAuSqEEagrUwjlh6cuD0E"

DB_NAME = "bins.db"

HEADERS = {
    "Accept-Version": "3",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

PREFIJOS_VALIDOS = {
    "4": "VISA",
    "51": "MASTERCARD", "52": "MASTERCARD", "53": "MASTERCARD",
    "54": "MASTERCARD", "55": "MASTERCARD",
    "22": "MASTERCARD", "23": "MASTERCARD", "24": "MASTERCARD",
    "25": "MASTERCARD", "26": "MASTERCARD", "27": "MASTERCARD",
    "34": "AMEX", "37": "AMEX",
    "6011": "DISCOVER", "65": "DISCOVER", "64": "DISCOVER",
    "35": "JCB", "2131": "JCB", "1800": "JCB",
    "30": "DINERS", "36": "DINERS", "38": "DINERS", "39": "DINERS",
    "62": "UNIONPAY",
}

BANDERAS = {
    "UNITED STATES": "🇺🇸", "USA": "🇺🇸", "MEXICO": "🇲🇽", "BRAZIL": "🇧🇷",
    "BRASIL": "🇧🇷", "ARGENTINA": "🇦🇷", "COLOMBIA": "🇨🇴", "CHILE": "🇨🇱",
    "PERU": "🇵🇪", "VENEZUELA": "🇻🇪", "ECUADOR": "🇪🇨", "SPAIN": "🇪🇸",
    "ESPAÑA": "🇪🇸", "FRANCE": "🇫🇷", "GERMANY": "🇩🇪", "UNITED KINGDOM": "🇬🇧",
    "UK": "🇬🇧", "CANADA": "🇨🇦", "ITALY": "🇮🇹", "JAPAN": "🇯🇵",
    "CHINA": "🇨🇳", "INDIA": "🇮🇳", "RUSSIA": "🇷🇺", "AUSTRALIA": "🇦🇺",
    "NETHERLANDS": "🇳🇱", "BELGIUM": "🇧🇪", "SWITZERLAND": "🇨🇭", "SWEDEN": "🇸🇪",
    "PORTUGAL": "🇵🇹", "IRELAND": "🇮🇪", "POLAND": "🇵🇱", "TURKEY": "🇹🇷",
    "SOUTH KOREA": "🇰🇷", "KOREA": "🇰🇷", "THAILAND": "🇹🇭", "INDONESIA": "🇮🇩",
    "MALAYSIA": "🇲🇾", "SINGAPORE": "🇸🇬", "PHILIPPINES": "🇵🇭", "VIETNAM": "🇻🇳",
    "EGYPT": "🇪🇬", "SOUTH AFRICA": "🇿🇦", "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬",
    "UNITED ARAB EMIRATES": "🇦🇪", "SAUDI ARABIA": "🇸🇦", "ISRAEL": "🇮🇱",
    "GREECE": "🇬🇷", "CZECH REPUBLIC": "🇨🇿", "ROMANIA": "🇷🇴", "UKRAINE": "🇺🇦",
    "HUNGARY": "🇭🇺", "FINLAND": "🇫🇮", "NORWAY": "🇳🇴", "DENMARK": "🇩🇰",
    "AUSTRIA": "🇦🇹", "NEW ZEALAND": "🇳🇿", "PAKISTAN": "🇵🇰", "BANGLADESH": "🇧🇩",
    "CUBA": "🇨🇺", "URUGUAY": "🇺🇾", "PARAGUAY": "🇵🇾", "BOLIVIA": "🇧🇴",
    "COSTA RICA": "🇨🇷", "PANAMA": "🇵🇦", "GUATEMALA": "🇬🇹", "HONDURAS": "🇭🇳",
    "EL SALVADOR": "🇸🇻", "NICARAGUA": "🇳🇮", "DOMINICAN REPUBLIC": "🇩🇴",
}

def detectar_marca(bin_code):
    for length in [4, 2, 1]:
        prefijo = bin_code[:length]
        if prefijo in PREFIJOS_VALIDOS:
            return PREFIJOS_VALIDOS[prefijo]
    return None

def generar_bin():
    return str(secrets.randbelow(9) + 1) + ''.join([str(secrets.randbelow(10)) for _ in range(5)])

def generar_bin_valido():
    for _ in range(100):
        b = generar_bin()
        if detectar_marca(b):
            return b
    return None

def generar_fecha():
    return f"{secrets.randbelow(12)+1:02d}/{secrets.randbelow(6)+25}"

def generar_extra(b):
    return f"{b}xxxxxxxx/{generar_fecha()}"

def get_bandera(pais):
    pais_up = pais.upper().strip()
    for k, v in BANDERAS.items():
        if k in pais_up:
            return v
    return "🌍"

def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS bins_enviados (bin TEXT PRIMARY KEY, fecha TEXT)")
    conn.commit(); conn.close()

def bin_ya_enviado(b):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT bin FROM bins_enviados WHERE bin = ?", (b,)); r = c.fetchone(); conn.close()
    return r is not None

def guardar_bin(b):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bins_enviados VALUES (?, ?)", (b, datetime.now().isoformat()))
    conn.commit(); conn.close()

# ============================================
# APIs
# ============================================

def verificar_binlist(b):
    try:
        r = requests.get(f"https://lookup.binlist.net/{b}", headers=HEADERS, timeout=10)
        logger.info(f"[binlist] {b} -> {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            return {
                "pais": d.get("country", {}).get("name", "UNKNOWN").upper(),
                "banco": d.get("bank", {}).get("name", "UNKNOWN").upper(),
                "tipo": (d.get("type") or "UNKNOWN").upper(),
                "marca": (d.get("scheme") or "UNKNOWN").upper(),
                "nivel": (d.get("brand") or "UNKNOWN").upper()
            }
    except Exception as e:
        logger.error(f"[binlist] Error {b}: {e}")
    return None

def verificar_bincheck(b):
    try:
        r = requests.get(f"https://bincheck.io/es/details/{b}", headers=HEADERS, timeout=10)
        logger.info(f"[bincheck] {b} -> {r.status_code}")
        if r.status_code != 200:
            return None
        html = r.text
        info = {}
        patterns = {
            "banco": [r'Bank[:\s]*</[^>]+>\s*<[^>]+>([^<]+)<', r'"bank"\s*:\s*"([^"]+)"'],
            "pais": [r'Country[:\s]*</[^>]+>\s*<[^>]+>([^<]+)<', r'"country"\s*:\s*"([^"]+)"'],
            "tipo": [r'Type[:\s]*</[^>]+>\s*<[^>]+>([^<]+)<', r'"type"\s*:\s*"([^"]+)"'],
            "marca": [r'Scheme[:\s]*</[^>]+>\s*<[^>]+>([^<]+)<', r'"scheme"\s*:\s*"([^"]+)"'],
            "nivel": [r'Brand[:\s]*</[^>]+>\s*<[^>]+>([^<]+)<', r'"brand"\s*:\s*"([^"]+)"'],
        }
        for campo, pats in patterns.items():
            for pat in pats:
                m = re.search(pat, html, re.IGNORECASE)
                if m:
                    valor = m.group(1).strip()[:80]
                    if valor and valor.lower() not in ['unknown', 'n/a', '']:
                        info[campo] = valor.upper()
                        break
        if info:
            return {
                "pais": info.get("pais", "UNKNOWN"),
                "banco": info.get("banco", "UNKNOWN"),
                "tipo": info.get("tipo", "UNKNOWN"),
                "marca": info.get("marca", "UNKNOWN"),
                "nivel": info.get("nivel", "UNKNOWN")
            }
    except Exception as e:
        logger.error(f"[bincheck] Error {b}: {e}")
    return None

def verificar_bincodes(b):
    if not BINCODES_API_KEY:
        return None
    try:
        url = f"https://api.bincodes.com/bin/json/{b}/{BINCODES_API_KEY}/"
        r = requests.get(url, timeout=10)
        logger.info(f"[bincodes] {b} -> {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            return {
                "pais": (d.get("country") or "UNKNOWN").upper(),
                "banco": (d.get("bank") or "UNKNOWN").upper(),
                "tipo": (d.get("card") or "UNKNOWN").upper(),
                "marca": (d.get("brand") or "UNKNOWN").upper(),
                "nivel": (d.get("level") or "UNKNOWN").upper(),
            }
    except Exception as e:
        logger.error(f"[bincodes] Error {b}: {e}")
    return None

def verificar_paralelo(b):
    inicio = datetime.now()
    marca_local = detectar_marca(b)
    
    info_final = {
        "bin": b, "pais": "UNKNOWN", "banco": "UNKNOWN",
        "tipo": "UNKNOWN", "marca": marca_local or "UNKNOWN", "nivel": "UNKNOWN"
    }
    
    info1 = info2 = info3 = None
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            fut1 = executor.submit(verificar_binlist, b)
            fut2 = executor.submit(verificar_bincheck, b)
            fut3 = executor.submit(verificar_bincodes, b) if BINCODES_API_KEY else None
            
            try: info1 = fut1.result(timeout=15)
            except: pass
            try: info2 = fut2.result(timeout=15)
            except: pass
            if fut3:
                try: info3 = fut3.result(timeout=15)
                except: pass
    except Exception as e:
        logger.error(f"Error paralelo: {e}")
    
    for info in [info1, info2, info3]:
        if info and info.get("banco") and info["banco"] != "UNKNOWN":
            info_final.update(info)
            break
    
    if info_final["banco"] == "UNKNOWN":
        for info in [info1, info2, info3]:
            if info:
                info_final.update(info)
                break
    
    if info_final["marca"] == "UNKNOWN" and marca_local:
        info_final["marca"] = marca_local
    
    duracion = (datetime.now() - inicio).total_seconds()
    logger.info(f"[paralelo] {b} verificado en {duracion:.2f}s")
    
    return info_final

def formatear(info):
    b = info["bin"]
    extra1 = generar_extra(b)
    extra2 = generar_extra(b)
    bandera = get_bandera(info['pais'])
    tipo_completo = f"{info['marca']} {info['tipo']} {info['nivel']}".strip()
    
    msg = f"""<a href="{LINK_BOT}">★</a>𝐌𝐀𝐒𝐓𝐄𝐑 𝐒𝐂𝐑𝐀𝐏𝐏 #{b}
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
 <a href="{LINK_BOT}">✓</a>BIN <code>{b}</code>
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
 <a href="{LINK_PROGRAMADOR}">∆</a> Info » {tipo_completo}
 <a href="{LINK_PROGRAMADOR}">∆</a> Country » {bandera} {info['pais']}
 <a href="{LINK_PROGRAMADOR}">∆</a> Bank » {info['banco']}
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
<a href="{LINK_PROGRAMADOR}">∆</a> Extra:
<code>{extra1}</code>
<code>{extra2}</code>
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━"""
    
    kb = [
        [InlineKeyboardButton("💻 Programmer / Seller", url=LINK_PROGRAMADOR)],
        [
            InlineKeyboardButton("👑 Seller / Owner", url=LINK_SELLER_OWNER),
            InlineKeyboardButton("🛒 Seller", url=LINK_SELLER_1)
        ],
        [InlineKeyboardButton("🛒 Seller", url=LINK_SELLER_2)]
    ]
    return msg, InlineKeyboardMarkup(kb)

# ============================================
# ✅ LOOP CON EVENT LOOP DEL BOT (sin hilos)
# ============================================

async def loop_envio(bot):
    """Loop que usa el mismo event loop del bot"""
    logger.info("🚀 Loop de envío iniciado")
    
    while True:
        try:
            b = generar_bin_valido()
            if not b:
                await asyncio.sleep(3)
                continue
            
            if bin_ya_enviado(b):
                continue
            
            # Verificar (esto es bloqueante pero en thread separado)
            info = await asyncio.get_event_loop().run_in_executor(None, verificar_paralelo, b)
            msg, kb = formatear(info)
            
            try:
                await bot.send_video(
                    chat_id=CANAL_BINS_ID,
                    video=VIDEO_FILE_ID,
                    caption=msg,
                    parse_mode='HTML',
                    reply_markup=kb
                )
                guardar_bin(b)
                logger.info(f"✅ BIN {b} enviado con video")
            except Exception as e:
                logger.error(f"❌ Error VIDEO: {e}")
                try:
                    await bot.send_message(chat_id=CANAL_BINS_ID, text=msg, parse_mode='HTML', reply_markup=kb)
                    guardar_bin(b)
                    logger.info(f"✅ BIN {b} enviado (texto)")
                except Exception as e2:
                    logger.error(f"❌ Error TEXTO: {e2}")
            
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Error loop: {e}")
            await asyncio.sleep(3)

async def cmd_start(update, context):
    if not update.message: return
    estado = "✅ Activo" if BINCODES_API_KEY else "⚠️ Sin API key bincodes"
    await update.message.reply_text(f"✅ Bot activo\n📊 bincodes: {estado}")

async def cmd_clean(update, context):
    if not update.message: return
    if update.effective_user.id != OWNER_ID: return
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("DELETE FROM bins_enviados"); conn.commit(); conn.close()
    await update.message.reply_text("🗑️ DB limpiada.")

async def cmd_testvideo(update, context):
    if not update.message: return
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text("⏳ Probando video...")
    try:
        msg = await context.bot.send_video(
            chat_id=CANAL_BINS_ID,
            video=VIDEO_FILE_ID,
            caption="🧪 TEST VIDEO"
        )
        await update.message.reply_text(f"✅ Video OK. Msg ID: {msg.message_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "📌 Estado"),
        BotCommand("clean", "🗑️ Limpiar DB"),
        BotCommand("testvideo", "🧪 Probar video")
    ])
    # ✅ Crear tarea asíncrona en el MISMO event loop
    asyncio.create_task(loop_envio(app.bot))
    logger.info("Tarea de envío creada")

def main():
    init_db()
    logger.info("Iniciando bot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clean", cmd_clean))
    app.add_handler(CommandHandler("testvideo", cmd_testvideo))
    app.post_init = post_init
    logger.info("Bot iniciado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()