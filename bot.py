import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
import json
from datetime import datetime
import requests

class VPNManager:
    def __init__(self):
        self.vpn_extensions = {
            "touchvpn": {
                "id": "bihmplhobchoageeokmgbdihknkjbknd",
                "crx_url": "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=109.0&x=id%3Dbihmplhobchoageeokmgbdihknkjbknd%26installsource%3Dwebstore%26uc",
                "crx_file": "touch_vpn.crx"
            },
            "hotspotshield": {
                "id": "nlbejmccbhkncgokjcmghpfloaajcffj", 
                "crx_url": "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=109.0&x=id%3Dnlbejmccbhkncgokjcmghpfloaajcffj%26installsource%3Dwebstore%26uc",
                "crx_file": "hotspot_shield.crx"
            }
        }
    
    def download_crx_file(self, url, output_path):
        """Download CRX file dari URL"""
        try:
            response = requests.get(url, stream=True)
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"Downloaded CRX to: {output_path}")
            return True
        except Exception as e:
            print(f"Error downloading CRX: {e}")
            return False
    
    def download_all_extensions(self):
        """Download semua VPN extensions"""
        for name, info in self.vpn_extensions.items():
            crx_path = f"extensions/{info['crx_file']}"
            if not os.path.exists(crx_path):
                os.makedirs("extensions", exist_ok=True)
                self.download_crx_file(info['crx_url'], crx_path)
    
    def get_random_vpn_crx(self):
        """Dapatkan path CRX acak, pastikan sudah didownload"""
        self.download_all_extensions()
        available_vpns = []
        for name, info in self.vpn_extensions.items():
            crx_path = f"extensions/{info['crx_file']}"
            if os.path.exists(crx_path):
                available_vpns.append((crx_path, name))
        
        if available_vpns:
            return random.choice(available_vpns)
        else:
            return None, None

class SeleniumBot:
    def __init__(self):
        self.setup_logging()
        self.ua = UserAgent()
        self.driver = None
        self.vpn_manager = VPNManager()
        self.session_data = {
            'session_start': None,
            'user_agent': None,
            'vpn_extension': None,
            'pages_visited': 0,
            'ads_closed': 0
        }
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi yang diperlukan"""
        chrome_options = Options()
        
        # Rotasi User Agent
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        self.session_data['user_agent'] = user_agent
        
        # Load VPN extension (hanya jika tidak di Render atau file ada)
        if not os.getenv('RENDER'):
            crx_path, vpn_name = self.vpn_manager.get_random_vpn_crx()
            if crx_path:
                chrome_options.add_extension(crx_path)
                self.session_data['vpn_extension'] = vpn_name
                self.logger.info(f"Loaded VPN extension: {vpn_name}")
        
        # Konfigurasi Chrome lainnya
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Untuk deploy di Render (headless)
        if os.getenv('RENDER'):
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            # Gunakan chromium yang tersedia
            chrome_options.binary_location = '/usr/bin/chromium' if os.path.exists('/usr/bin/chromium') else '/usr/bin/google-chrome'
        
        # Gunakan WebDriver Manager untuk mengelola driver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            self.logger.warning(f"WebDriverManager failed: {e}, trying direct Chrome")
            # Fallback ke Chrome system
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Tunggu extension load dan handle popup
        if not os.getenv('RENDER'):
            time.sleep(5)
            self.handle_extension_popup()
        
        self.logger.info(f"Browser started with User Agent: {user_agent}")
    
    def handle_extension_popup(self):
        """Handle extension popup window"""
        try:
            if len(self.driver.window_handles) > 1:
                for handle in self.driver.window_handles[1:]:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
        except Exception as e:
            self.logger.warning(f"Error handling extension popup: {e}")
    
    # ... (method lainnya tetap sama seperti sebelumnya)

# Flask app dan bagian lainnya tetap sama
from flask import Flask, jsonify, render_template
import threading

app = Flask(__name__)
bot_instance = None

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    if bot_instance:
        return jsonify(bot_instance.get_session_stats())
    return jsonify({'status': 'Bot not running'})

@app.route('/api/control/<action>')
def control_bot(action):
    global bot_instance
    if action == 'start' and not bot_instance:
        def run_bot():
            global bot_instance
            bot_instance = SeleniumBot()
            target_urls = [
                "https://cryptoajah.blogspot.com",  # GANTI DENGAN URL TARGET ANDA
                "https://cryptoajah.blogspot.com/2025/10/panduan-lengkap-berinvestasi.html"  # GANTI DENGAN URL TARGET ANDA
            ]
            bot_instance.run_session(target_urls)
        
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'Bot started'})
    elif action == 'stop' and bot_instance:
        if bot_instance.driver:
            bot_instance.driver.quit()
        bot_instance = None
        return jsonify({'status': 'Bot stopped'})
    else:
        return jsonify({'status': 'Invalid action'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
