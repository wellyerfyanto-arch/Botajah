import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

class AdvancedSeleniumBot:
    def __init__(self):
        self.ua = UserAgent()
        self.driver = None
        self.session_data = {
            'session_start': None,
            'user_agent': None,
            'vpn_extension': None,
            'google_domain': None,
            'pages_visited': 0,
            'ads_closed': 0,
            'data_leak_checked': False,
            'current_step': 'Initializing'
        }

    def setup_driver(self):
        """Setup Chrome driver dengan semua konfigurasi"""
        chrome_options = Options()
        
        # 1. Rotasi User Agent (setiap session berbeda)
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        self.session_data['user_agent'] = user_agent
        logger.info(f"🔄 User Agent: {user_agent}")
        
        # 2. VPN Extension (Touch VPN)
        try:
            crx_path = "touchvpn.crx"
            if os.path.exists(crx_path) and os.path.getsize(crx_path) > 1000:
                chrome_options.add_extension(crx_path)
                self.session_data['vpn_extension'] = 'Touch VPN'
                logger.info("✅ VPN Extension: Touch VPN loaded")
        except Exception as e:
            logger.warning(f"⚠️ VPN Extension: {e}")

        # Konfigurasi Chrome untuk Render
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Gunakan Chrome dari instalasi manual
        chrome_options.binary_location = '/tmp/chrome/chrome'
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Chrome driver started successfully")
            
            # Handle VPN popup jika ada
            time.sleep(3)
            self.handle_vpn_popup()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Chrome: {e}")
            return False

    def handle_vpn_popup(self):
        """Handle VPN extension popup"""
        try:
            if len(self.driver.window_handles) > 1:
                for handle in self.driver.window_handles[1:]:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
        except Exception as e:
            logger.warning(f"VPN popup handling: {e}")

    def change_google_location(self):
        """Rubah titik Google sesuai lokasi VPN"""
        google_domains = {
            "US": "https://www.google.com",
            "UK": "https://www.google.co.uk", 
            "Japan": "https://www.google.co.jp",
            "Australia": "https://www.google.com.au",
            "Germany": "https://www.google.de",
            "France": "https://www.google.fr",
            "Singapore": "https://www.google.com.sg",
            "Indonesia": "https://www.google.co.id"
        }
        
        location = random.choice(list(google_domains.keys()))
        domain = google_domains[location]
        
        self.session_data['current_step'] = f"Changing Google to {location}"
        logger.info(f"🌍 Changing Google location: {location} -> {domain}")
        
        try:
            self.driver.get(domain)
            time.sleep(3)
            self.session_data['google_domain'] = domain
            return True
        except Exception as e:
            logger.error(f"❌ Failed to change Google location: {e}")
            return False

    def check_data_leak(self):
        """Cek kebocoran data"""
        self.session_data['current_step'] = "Checking data leak"
        logger.info("🔍 Checking data leak...")
        
        try:
            self.driver.get("https://ipleak.net")
            time.sleep(5)
            
            # Cari informasi IP
            ip_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'IP address')]")
            if ip_elements:
                ip_info = ip_elements[0].text[:100]
                logger.info(f"📊 IP Check: {ip_info}")
            
            self.session_data['data_leak_checked'] = True
            return True
        except Exception as e:
            logger.error(f"❌ Data leak check failed: {e}")
            return False

    def visit_target_url(self, url):
        """Buka link target"""
        self.session_data['current_step'] = f"Visiting {url}"
        logger.info(f"🌐 Visiting target URL: {url}")
        
        try:
            self.driver.get(url)
            self.session_data['pages_visited'] += 1
            time.sleep(random.uniform(3, 6))
            return True
        except Exception as e:
            logger.error(f"❌ Failed to visit {url}: {e}")
            return False

    def smart_scroll(self, direction="down"):
        """Scroll dengan durasi acak setiap session"""
        durations = {
            "down": random.uniform(8, 15),
            "up": random.uniform(5, 12)
        }
        
        duration = durations[direction]
        self.session_data['current_step'] = f"Scrolling {direction} ({duration:.1f}s)"
        logger.info(f"📜 Scrolling {direction} for {duration:.2f} seconds")
        
        start_time = time.time()
        scroll_pause_time = 0.1
        
        try:
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if direction == "down":
                current_position = 0
                while current_position < scroll_height and (time.time() - start_time) < duration:
                    current_position += random.randint(50, 150)
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(scroll_pause_time)
            else:  # up
                current_position = scroll_height
                while current_position > 0 and (time.time() - start_time) < duration:
                    current_position -= random.randint(50, 150)
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(scroll_pause_time)
                    
            return True
        except Exception as e:
            logger.warning(f"Scroll {direction} interrupted: {e}")
            return False

    def click_random_post(self):
        """Buka link postingan acak"""
        self.session_data['current_step'] = "Clicking random post"
        logger.info("🔗 Looking for posts to click...")
        
        try:
            post_selectors = [
                "a[href*='post']", "a[href*='article']", "a[href*='blog']",
                "a[class*='post']", "a[class*='article']", ".post-title a",
                ".entry-title a", "h2 a", "h3 a", ".title a"
            ]
            
            all_links = []
            for selector in post_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_links.extend(links)
                except:
                    continue
            
            valid_links = []
            for link in all_links:
                try:
                    if link.is_displayed() and link.is_enabled():
                        valid_links.append(link)
                except:
                    continue
            
            if valid_links:
                chosen_link = random.choice(valid_links)
                post_url = chosen_link.get_attribute('href') or "Unknown URL"
                logger.info(f"📖 Clicking post: {post_url[:80]}...")
                chosen_link.click()
                time.sleep(random.uniform(4, 8))
                return True
            else:
                logger.warning("No posts found to click")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to click post: {e}")
            return False

    def handle_ads(self):
        """Lewati iklan dengan berbagai keyword"""
        self.session_data['current_step'] = "Handling ads"
        
        close_selectors = [
            "button[aria-label*='close' i]", "button[class*='close' i]",
            "div[class*='close' i]", "span[class*='close' i]", "a[class*='close' i]",
            ".close-btn", ".ad-close", ".skip-button", "[data-dismiss='modal']"
        ]
        
        for selector in close_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            self.session_data['ads_closed'] += 1
                            logger.info(f"✅ Closed ad with selector: {selector}")
                            time.sleep(1)
                            return True
                    except:
                        continue
            except:
                continue
        
        close_texts = ['tutup', 'close', 'skip', 'lanjut', 'lewati', 'skip ad']
        for text in close_texts:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            self.session_data['ads_closed'] += 1
                            logger.info(f"✅ Closed ad with text: {text}")
                            time.sleep(1)
                            return True
                    except:
                        continue
            except:
                continue
        
        return False

    def refresh_page(self):
        """Refresh halaman"""
        self.session_data['current_step'] = "Refreshing page"
        logger.info("🔄 Refreshing page...")
        
        try:
            self.driver.refresh()
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"❌ Refresh failed: {e}")
            return False

    def clear_cache(self):
        """Clear cache dan history"""
        self.session_data['current_step'] = "Clearing cache"
        logger.info("🧹 Clearing cache and history...")
        
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            logger.info("✅ Cache cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Cache clear failed: {e}")
            return False

    def get_session_stats(self):
        return {
            'session_start': self.session_data['session_start'],
            'user_agent': self.session_data['user_agent'],
            'vpn_extension': self.session_data['vpn_extension'],
            'google_domain': self.session_data['google_domain'],
            'pages_visited': self.session_data['pages_visited'],
            'ads_closed': self.session_data['ads_closed'],
            'data_leak_checked': self.session_data['data_leak_checked'],
            'current_step': self.session_data['current_step'],
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Running'
        }

    def run_complete_session(self, target_urls):
        """Jalankan session lengkap dan ulang dari awal"""
        self.session_data['session_start'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.setup_driver():
            logger.error("❌ Cannot start bot - driver setup failed")
            return
        
        logger.info("🚀 Starting complete bot session...")
        
        session_count = 0
        while True:
            try:
                session_count += 1
                logger.info(f"🔄 Starting complete session #{session_count}")
                
                # 1. Rotasi User Agent & VPN (sudah di setup_driver)
                # 2. Rubah titik Google
                self.change_google_location()
                
                # 3. Cek kebocoran data
                self.check_data_leak()
                
                # 4. Buka link target
                target_url = random.choice(target_urls)
                self.visit_target_url(target_url)
                
                # 5. Scroll down (durasi random)
                self.smart_scroll("down")
                
                # 6. Scroll up (durasi random)  
                self.smart_scroll("up")
                
                # 7. Buka postingan
                self.click_random_post()
                
                # 8. Handle iklan
                for _ in range(3):
                    self.handle_ads()
                    time.sleep(1)
                
                # 9. Refresh
                self.refresh_page()
                
                # 10. Clear cache
                self.clear_cache()
                
                # 11. Tunggu sebelum mengulang
                wait_time = random.uniform(60, 180)
                logger.info(f"⏰ Waiting {wait_time:.1f}s before next session...")
                self.session_data['current_step'] = f"Waiting {wait_time:.1f}s"
                time.sleep(wait_time)
                
                logger.info("🔄 Restarting complete session from beginning...")
                
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
    <title>Selenium Bot Monitor</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { text-align: center; background: #2c3e50; color: white; padding: 20px; border-radius: 10px; }
        .controls { text-align: center; margin: 20px 0; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-start { background: #27ae60; color: white; }
        .btn-stop { background: #e74c3c; color: white; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }
        .log-container { background: #2c3e50; color: #27ae60; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto; font-family: monospace; }
        .status-running { color: #27ae60; }
        .status-stopped { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Selenium Bot Monitor</h1>
        </div>
        
        <div class="controls">
            <button class="btn btn-start" onclick="controlBot('start')">🚀 Start Bot</button>
            <button class="btn btn-stop" onclick="controlBot('stop')">🛑 Stop Bot</button>
        </div>

        <div class="stats">
            <div class="stat-card"><h3>Status</h3><div class="stat-value status-stopped" id="status">Stopped</div></div>
            <div class="stat-card"><h3>Pages Visited</h3><div class="stat-value" id="pages">0</div></div>
            <div class="stat-card"><h3>Ads Closed</h3><div class="stat-value" id="ads">0</div></div>
            <div class="stat-card"><h3>VPN</h3><div class="stat-value" id="vpn">-</div></div>
            <div class="stat-card"><h3>Google Domain</h3><div class="stat-value" id="googleDomain">-</div></div>
            <div class="stat-card"><h3>Current Step</h3><div class="stat-value" id="currentStep">-</div></div>
        </div>
        
        <div class="log-container" id="logContainer">
            <div>> System ready. Click "Start Bot" to begin.</div>
        </div>
    </div>

    <script>
        function updateStats() {
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('status').textContent = data.status || 'Stopped';
                document.getElementById('status').className = 'stat-value ' + (data.status === 'Running' ? 'status-running' : 'status-stopped');
                document.getElementById('pages').textContent = data.pages_visited || 0;
                document.getElementById('ads').textContent = data.ads_closed || 0;
                document.getElementById('vpn').textContent = data.vpn_extension || '-';
                document.getElementById('googleDomain').textContent = data.google_domain || '-';
                document.getElementById('currentStep').textContent = data.current_step || '-';
            });
        }

        function controlBot(action) {
            fetch(`/api/control/${action}`).then(r => r.json()).then(data => {
                addLog(`${action}: ${data.status}`);
            });
        }

        function addLog(message) {
            const logContainer = document.getElementById('logContainer');
            const timestamp = new Date().toLocaleTimeString();
            logContainer.innerHTML += `<div>[${timestamp}] ${message}</div>`;
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        setInterval(updateStats, 3000);
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
        def run_bot():
            global bot_instance
            bot_instance = AdvancedSeleniumBot()
            # ⚠️ GANTI URL TARGET ANDA DI SINI ⚠️
            target_urls = [
                "https://www.cryptoajah.blogspot.com",
                "https://www.cryptoajah.blogspot.com",
                "https://cryptoajah.blogspot.com"
            ]
            bot_instance.run_complete_session(target_urls)
        
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'Bot started successfully'})
    
    elif action == 'stop' and bot_instance:
    
