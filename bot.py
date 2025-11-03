import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from datetime import datetime
import requests
from flask import Flask, jsonify, render_template_string
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_instance = None

class SeleniumBot:
    def __init__(self):
        self.ua = UserAgent()
        self.driver = None
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
        
        # Coba load VPN extension jika ada
        try:
            crx_path = "extensions/touch_vpn.crx"
            if os.path.exists(crx_path) and os.path.getsize(crx_path) > 1000:
                chrome_options.add_extension(crx_path)
                self.session_data['vpn_extension'] = 'touchvpn'
                logger.info("VPN extension loaded")
        except Exception as e:
            logger.warning(f"VPN not loaded: {e}")

        # Konfigurasi untuk environment Render
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Optional: percepat loading
        
        # Gunakan chromium-browser yang tersedia di Render
        chrome_options.binary_location = self.find_chrome_binary()
        
        logger.info(f"Using Chrome binary: {chrome_options.binary_location}")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Chrome driver started successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Chrome: {e}")
            return False

    def find_chrome_binary(self):
        """Cari Chrome/Chromium binary yang tersedia di system"""
        possible_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser', 
            '/usr/bin/chromium',
            '/app/.apt/usr/bin/google-chrome',
            '/usr/local/bin/chromium'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found browser at: {path}")
                return path
        
        logger.warning("No Chrome/Chromium found, using system default")
        return None

    def smart_scroll(self, direction="down", duration=None):
        """Scroll halaman dengan durasi acak"""
        if duration is None:
            duration = random.uniform(3, 8)
        
        logger.info(f"Scrolling {direction} for {duration:.2f}s")
        
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
        """Coba tutup iklan dengan berbagai selector"""
        close_selectors = [
            "button[aria-label*='close' i]",
            "button[class*='close' i]",
            ".close-btn",
            ".ad-close", 
            ".skip-button",
            "[data-dismiss='modal']"
        ]
        
        for selector in close_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        self.session_data['ads_closed'] += 1
                        logger.info(f"✅ Closed ad: {selector}")
                        time.sleep(1)
                        return True
            except Exception:
                continue
        
        # Coba dengan teks
        close_texts = ['close', 'skip', 'tutup', 'lanjut']
        for text in close_texts:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        self.session_data['ads_closed'] += 1
                        logger.info(f"✅ Closed ad with text: {text}")
                        time.sleep(1)
                        return True
            except Exception:
                continue
        
        return False

    def visit_website(self, url):
        """Kunjungi website dengan interaksi lengkap"""
        try:
            logger.info(f"🌐 Visiting: {url}")
            self.driver.get(url)
            self.session_data['pages_visited'] += 1
            
            # Tunggu page load
            time.sleep(random.uniform(2, 5))
            
            # Handle initial ads
            self.handle_ads()
            
            # Scroll down
            self.smart_scroll("down", random.uniform(4, 8))
            
            # Scroll up
            self.smart_scroll("up", random.uniform(2, 5))
            
            # Click random links
            self.click_random_links()
            
            # Handle ads lagi
            self.handle_ads()
            
            logger.info(f"✅ Successfully processed: {url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error visiting {url}: {e}")
            return False

    def click_random_links(self):
        """Klik link acak di halaman"""
        try:
            # Cari semua link
            links = self.driver.find_elements(By.TAG_NAME, "a")
            valid_links = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if (href and href.startswith('http') and 
                        link.is_displayed() and link.is_enabled() and
                        len(text) > 3 and len(text) < 100):
                        valid_links.append(link)
                except Exception:
                    continue
            
            if valid_links:
                # Pilih random link dari 5 pertama yang valid
                chosen = random.choice(valid_links[:5])
                href = chosen.get_attribute('href')
                logger.info(f"🔗 Clicking random link: {href}")
                chosen.click()
                
                # Tunggu page load
                time.sleep(random.uniform(3, 6))
                
                # Handle ads di page baru
                self.handle_ads()
                
                # Kembali ke previous page
                self.driver.back()
                time.sleep(2)
                
                return True
                
        except Exception as e:
            logger.warning(f"Could not click links: {e}")
        
        return False

    def clear_data(self):
        """Clear browser data"""
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            logger.info("🧹 Cleared browser data")
        except Exception as e:
            logger.warning(f"Warning clearing data: {e}")

    def get_session_stats(self):
        """Dapatkan statistik sesi"""
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
        """Jalankan bot utama"""
        self.session_data['session_start'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Setup driver
        if not self.setup_driver():
            logger.error("❌ Failed to setup driver, stopping bot")
            return
        
        logger.info("🚀 Bot started successfully!")
        
        session_count = 0
        while True:
            try:
                session_count += 1
                logger.info(f"🔄 Starting session #{session_count}")
                
                # Pilih URL acak
                url = random.choice(urls)
                
                # Kunjungi website
                self.visit_website(url)
                
                # Clear data
                self.clear_data()
                
                # Tunggu sebelum sesi berikutnya
                wait_time = random.uniform(45, 120)
                logger.info(f"⏰ Waiting {wait_time:.1f} seconds until next session...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"💥 Session error: {e}")
                logger.info("🔄 Restarting in 30 seconds...")
                time.sleep(30)

# Flask Routes
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bot Monitor</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .controls {
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .btn {
            padding: 12px 30px;
            margin: 0 10px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-start {
            background: #28a745;
            color: white;
        }
        .btn-stop {
            background: #dc3545;
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .stats {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
            text-align: center;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .status-running { color: #28a745; }
        .status-stopped { color: #dc3545; }
        .log-container {
            background: #1e1e1e;
            color: #00ff00;
            padding: 20px;
            margin: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            height: 300px;
            overflow-y: auto;
        }
        .log-entry {
            margin: 5px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Selenium Bot Monitor</h1>
            <p>Real-time monitoring and control</p>
        </div>
        
        <div class="controls">
            <button class="btn btn-start" onclick="controlBot('start')">🚀 Start Bot</button>
            <button class="btn btn-stop" onclick="controlBot('stop')">🛑 Stop Bot</button>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Status</h3>
                <div class="stat-value status-stopped" id="status">Stopped</div>
            </div>
            <div class="stat-card">
                <h3>Pages Visited</h3>
                <div class="stat-value" id="pages">0</div>
            </div>
            <div class="stat-card">
                <h3>Ads Closed</h3>
                <div class="stat-value" id="ads">0</div>
            </div>
            <div class="stat-card">
                <h3>VPN Extension</h3>
                <div class="stat-value" id="vpn">-</div>
            </div>
            <div class="stat-card">
                <h3>Session Start</h3>
                <div class="stat-value" id="sessionStart">-</div>
            </div>
            <div class="stat-card">
                <h3>Current Time</h3>
                <div class="stat-value" id="currentTime">-</div>
            </div>
        </div>
        
        <div class="log-container" id="logContainer">
            <div class="log-entry">>> System ready. Click "Start Bot" to begin.</div>
        </div>
    </div>

    <script>
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status || 'Stopped';
                    document.getElementById('status').className = 'stat-value ' + 
                        (data.status === 'Running' ? 'status-running' : 'status-stopped');
                    document.getElementById('pages').textContent = data.pages_visited || 0;
                    document.getElementById('ads').textContent = data.ads_closed || 0;
                    document.getElementById('vpn').textContent = data.vpn_extension || '-';
                    document.getElementById('sessionStart').textContent = data.session_start || '-';
                    document.getElementById('currentTime').textContent = data.current_time || '-';
                })
                .catch(error => {
                    console.error('Error fetching stats:', error);
                });
        }

        function controlBot(action) {
            fetch(`/api/control/${action}`)
                .then(response => response.json())
                .then(data => {
                    addLog(`Action: ${action} - ${data.status}`);
                    if (action === 'start') {
                        // Start polling for stats
                        setInterval(updateStats, 3000);
                    }
                })
                .catch(error => {
                    addLog(`Error: ${error.message}`);
                });
        }

        function addLog(message) {
            const logContainer = document.getElementById('logContainer');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.textContent = `[${timestamp}] ${message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // Auto-update stats every 5 seconds
        setInterval(updateStats, 5000);
        updateStats(); // Initial update
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
        def run_bot():
            global bot_instance
            bot_instance = SeleniumBot()
            # ⚠️ GANTI URL TARGET ANDA DI BAWAH INI ⚠️
            target_urls = [
                "https://www.wikipedia.org",
                "https://www.github.com",
                "https://stackoverflow.com",
                "https://www.reddit.com",
                "https://www.quora.com"
            ]
            bot_instance.run_bot(target_urls)
        
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'Bot started successfully'})
    
    elif action == 'stop' and bot_instance:
        if bot_instance.driver:
            bot_instance.driver.quit()
        bot_instance = None
        return jsonify({'status': 'Bot stopped successfully'})
    
    return jsonify({'status': 'No action taken'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
