import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
import json
from datetime import datetime
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleVPNManager:
    def __init__(self):
        self.vpn_extensions = {
            "touchvpn": {
                "crx_url": "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=109.0&x=id%3Dbihmplhobchoageeokmgbdihknkjbknd%26installsource%3Dwebstore%26uc",
                "crx_file": "touch_vpn.crx"
            }
        }
    
    def setup_vpn(self, chrome_options):
        """Setup VPN extension jika file tersedia"""
        try:
            crx_path = "extensions/touch_vpn.crx"
            if os.path.exists(crx_path) and os.path.getsize(crx_path) > 1000:  # Pastikan file tidak kosong
                chrome_options.add_extension(crx_path)
                logger.info("VPN extension loaded")
                return "touchvpn"
        except Exception as e:
            logger.warning(f"Could not load VPN: {e}")
        return None

class SeleniumBot:
    def __init__(self):
        self.ua = UserAgent()
        self.driver = None
        self.vpn_manager = SimpleVPNManager()
        self.session_data = {
            'session_start': None,
            'user_agent': None,
            'vpn_extension': None,
            'pages_visited': 0,
            'ads_closed': 0
        }
    
    def setup_driver(self):
        """Setup Chrome driver untuk Render"""
        chrome_options = Options()
        
        # Rotasi User Agent
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        self.session_data['user_agent'] = user_agent
        
        # Setup VPN (jika tersedia)
        vpn_name = self.vpn_manager.setup_vpn(chrome_options)
        self.session_data['vpn_extension'] = vpn_name
        
        # Konfigurasi untuk Render
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Untuk Chrome di Render
        if os.path.exists('/app/chrome/chrome'):
            chrome_options.binary_location = '/app/chrome/chrome'
        
        try:
            # Coba gunakan ChromeDriver dari system
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver started successfully")
        except Exception as e:
            logger.error(f"Failed to start Chrome: {e}")
            raise
    
    def smart_scroll(self, direction="down", duration=None):
        """Scroll halaman dengan durasi acak"""
        if duration is None:
            duration = random.uniform(3, 8)
        
        logger.info(f"Scrolling {direction} for {duration:.2f} seconds")
        
        start_time = time.time()
        scroll_pause_time = 0.1
        
        scroll_height = self.driver.execute_script("return document.body.scrollHeight")
        
        if direction == "down":
            current_position = 0
            while current_position < scroll_height and (time.time() - start_time) < duration:
                current_position += random.randint(100, 300)
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(scroll_pause_time)
        else:  # up
            current_position = scroll_height
            while current_position > 0 and (time.time() - start_time) < duration:
                current_position -= random.randint(100, 300)
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(scroll_pause_time)
    
    def handle_ads(self):
        """Coba tutup iklan"""
        close_selectors = [
            "button[aria-label*='close' i]",
            "button[class*='close' i]",
            ".close-btn",
            ".ad-close",
            ".skip-button"
        ]
        
        for selector in close_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed():
                        button.click()
                        self.session_data['ads_closed'] += 1
                        logger.info(f"Closed ad: {selector}")
                        time.sleep(1)
                        return True
            except:
                continue
        return False
    
    def visit_website(self, url):
        """Kunjungi website dengan interaksi"""
        try:
            self.driver.get(url)
            self.session_data['pages_visited'] += 1
            logger.info(f"Visited: {url}")
            
            time.sleep(random.uniform(2, 5))
            
            # Scroll down
            self.smart_scroll("down", random.uniform(5, 10))
            
            # Scroll up
            self.smart_scroll("up", random.uniform(3, 7))
            
            # Handle ads
            self.handle_ads()
            
            # Click random links
            self.click_random_links()
            
            return True
            
        except Exception as e:
            logger.error(f"Error visiting {url}: {e}")
            return False
    
    def click_random_links(self):
        """Klik link acak"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            valid_links = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and ('http' in href) and link.is_displayed():
                        valid_links.append(link)
                except:
                    continue
            
            if valid_links:
                chosen = random.choice(valid_links[:10])  # Ambil dari 10 pertama
                chosen.click()
                logger.info("Clicked random link")
                time.sleep(random.uniform(3, 7))
                self.handle_ads()
                
        except Exception as e:
            logger.warning(f"Could not click links: {e}")
    
    def clear_data(self):
        """Clear browser data"""
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            logger.info("Cleared browser data")
        except Exception as e:
            logger.warning(f"Error clearing data: {e}")
    
    def get_session_stats(self):
        return {
            'session_start': self.session_data['session_start'],
            'user_agent': self.session_data['user_agent'],
            'vpn_extension': self.session_data['vpn_extension'],
            'pages_visited': self.session_data['pages_visited'],
            'ads_closed': self.session_data['ads_closed'],
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Running'
        }
    
    def run_bot(self, urls):
        """Jalankan bot"""
        self.session_data['session_start'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.setup_driver()
            
            while True:
                try:
                    url = random.choice(urls)
                    self.visit_website(url)
                    
                    self.clear_data()
                    
                    # Tunggu sebelum sesi berikutnya
                    wait_time = random.uniform(30, 90)
                    logger.info(f"Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    
                except Exception as e:
                    logger.error(f"Session error: {e}")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            logger.info("Bot stopped")
        finally:
            if self.driver:
                self.driver.quit()

# Flask App untuk Monitoring
from flask import Flask, jsonify, render_template_string
import threading

app = Flask(__name__)
bot_instance = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bot Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .card { background: #f5f5f5; padding: 20px; margin: 10px; border-radius: 5px; }
        .stat { margin: 5px 0; }
        .running { color: green; }
        .stopped { color: red; }
    </style>
</head>
<body>
    <h1>🤖 Selenium Bot Monitor</h1>
    
    <div class="card">
        <button onclick="startBot()">Start Bot</button>
        <button onclick="stopBot()">Stop Bot</button>
    </div>
    
    <div class="card">
        <h2>📊 Statistics</h2>
        <div id="stats">
            <div class="stat">Status: <span id="status" class="stopped">Stopped</span></div>
            <div class="stat">Pages Visited: <span id="pages">0</span></div>
            <div class="stat">Ads Closed: <span id="ads">0</span></div>
            <div class="stat">VPN: <span id="vpn">-</span></div>
            <div class="stat">Session Start: <span id="sessionStart">-</span></div>
        </div>
    </div>
    
    <script>
        function updateStats() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('status').className = data.status === 'Running' ? 'running' : 'stopped';
                    document.getElementById('pages').textContent = data.pages_visited || 0;
                    document.getElementById('ads').textContent = data.ads_closed || 0;
                    document.getElementById('vpn').textContent = data.vpn_extension || '-';
                    document.getElementById('sessionStart').textContent = data.session_start || '-';
                });
        }
        
        function startBot() {
            fetch('/api/control/start').then(() => {
                setTimeout(updateStats, 2000);
                setInterval(updateStats, 5000);
            });
        }
        
        function stopBot() {
            fetch('/api/control/stop').then(updateStats);
        }
        
        // Auto-update every 5 seconds
        setInterval(updateStats, 5000);
        updateStats();
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def get_stats():
    if bot_instance:
        return jsonify(bot_instance.get_session_stats())
    return jsonify({'status': 'Stopped'})

@app.route('/api/control/<action>')
def control_bot(action):
    global bot_instance
    if action == 'start' and not bot_instance:
        def run():
            global bot_instance
            bot_instance = SeleniumBot()
            # GANTI URL TARGET ANDA DI SINI
            target_urls = [
                "https://www.wikipedia.org",
                "https://www.github.com",
                "https://stackoverflow.com"
            ]
            bot_instance.run_bot(target_urls)
        
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'Bot started'})
    elif action == 'stop' and bot_instance:
        if bot_instance.driver:
            bot_instance.driver.quit()
        bot_instance = None
        return jsonify({'status': 'Bot stopped'})
    return jsonify({'status': 'Invalid action'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
