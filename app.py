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
from flask import Flask, jsonify, render_template, request
import threading
import json
import base64

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_manager = None

# Database proxy premium - GANTI DENGAN PROXY ANDA
PREMIUM_PROXY_LIST = [
    {
        'http': 'http://username:password@proxy-provider.com:8080',
        'https': 'https://username:password@proxy-provider.com:8080',
        'provider': 'BrightData',
        'country': 'US',
        'username': 'username',
        'password': 'password'
    },
    {
        'http': 'http://user:pass@proxy2-provider.com:8080',
        'https': 'https://user:pass@proxy2-provider.com:8080',
        'provider': 'Oxylabs', 
        'country': 'UK',
        'username': 'user',
        'password': 'pass'
    }
]

class ProxyManager:
    def __init__(self):
        self.premium_proxies = PREMIUM_PROXY_LIST.copy()
    
    def get_proxy(self):
        """Dapatkan proxy premium acak"""
        if not self.premium_proxies:
            return None
        
        proxy = random.choice(self.premium_proxies)
        logger.info(f"🔑 Using premium proxy: {proxy['provider']}")
        return proxy
    
    def test_proxy_connection(self, proxy_config):
        """Test koneksi proxy"""
        try:
            test_url = "http://httpbin.org/ip"
            response = requests.get(
                test_url, 
                proxies={
                    'http': proxy_config['http'],
                    'https': proxy_config['https']
                },
                timeout=10
            )
            if response.status_code == 200:
                return True, "Proxy connection successful"
            else:
                return False, f"Proxy returned status {response.status_code}"
        except Exception as e:
            return False, f"Proxy connection failed: {str(e)}"

class TabSession:
    def __init__(self, tab_id, user_agent, proxy=None, use_vpn=False):
        self.tab_id = tab_id
        self.user_agent = user_agent
        self.proxy = proxy
        self.use_vpn = use_vpn
        self.stats = {
            'pages_visited': 0,
            'ads_closed': 0,
            'current_url': None,
            'status': 'Ready',
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'proxy_provider': proxy.get('provider', 'None') if proxy else 'None',
            'proxy_country': proxy.get('country', 'None') if proxy else 'None'
        }

class AdvancedSeleniumBot:
    def __init__(self, config=None):
        self.ua = UserAgent()
        self.driver = None
        self.tabs = {}
        self.proxy_manager = ProxyManager()
        
        self.config = config or {
            'mode': 'direct',  # 'direct', 'proxy', 'vpn'
            'num_tabs': 1,
            'random_user_agent': True,
            'auto_rotate': True,
            'custom_proxies': []
        }
        
        self.session_data = {
            'session_start': None,
            'total_pages_visited': 0,
            'total_ads_closed': 0,
            'active_tabs': 0,
            'current_step': 'Initializing',
            'mode': self.config['mode']
        }

    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi yang tepat"""
        chrome_options = Options()
        
        # 1. Rotasi User Agent
        user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        logger.info(f"🔄 User Agent: {user_agent}")
        
        # 2. Konfigurasi Chrome untuk Render
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 3. VPN Extension (jika mode VPN)
        if self.config['mode'] == 'vpn':
            try:
                crx_path = "touchvpn.crx"
                if os.path.exists(crx_path) and os.path.getsize(crx_path) > 1000:
                    chrome_options.add_extension(crx_path)
                    logger.info("✅ VPN Extension: Touch VPN loaded")
            except Exception as e:
                logger.warning(f"⚠️ VPN Extension: {e}")

        # 4. Proxy Configuration (jika mode proxy)
        if self.config['mode'] == 'proxy':
            proxy = self.get_proxy_for_tab()
            if proxy:
                # Setup proxy melalui Chrome options
                proxy_url = proxy['http'].replace('http://', '').replace('https://', '')
                chrome_options.add_argument(f'--proxy-server={proxy_url}')
                logger.info(f"🔧 Proxy configured: {proxy['provider']}")
        
        # Gunakan Chrome dari instalasi manual
        chrome_options.binary_location = self.find_chrome_binary()
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Chrome driver started successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Chrome: {e}")
            return False

    def find_chrome_binary(self):
        """Cari Chrome binary yang tersedia"""
        paths = [
            '/tmp/chrome/chrome',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium'
        ]
        for path in paths:
            if os.path.exists(path):
                logger.info(f"🔍 Found Chrome at: {path}")
                return path
        logger.warning("⚠️ No Chrome binary found, using default")
        return None

    def get_proxy_for_tab(self):
        """Dapatkan proxy untuk tab"""
        if self.config['custom_proxies']:
            return random.choice(self.config['custom_proxies'])
        return self.proxy_manager.get_proxy()

    def create_tab_session(self, tab_id):
        """Buat session baru untuk tab"""
        user_agent = self.ua.random if self.config['random_user_agent'] else self.ua.chrome
        proxy = self.get_proxy_for_tab() if self.config['mode'] == 'proxy' else None
        use_vpn = self.config['mode'] == 'vpn'
        
        tab_session = TabSession(tab_id, user_agent, proxy, use_vpn)
        self.tabs[tab_id] = tab_session
        
        logger.info(f"🆕 Created tab {tab_id} - Mode: {self.config['mode']}")
        return tab_session

    def open_new_tab(self, url=None):
        """Buka tab baru"""
        try:
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('');")
            all_handles = self.driver.window_handles
            new_tab_handle = all_handles[-1]
            
            self.driver.switch_to.window(new_tab_handle)
            self.create_tab_session(new_tab_handle)
            
            # Set user agent untuk tab ini
            tab_session = self.tabs[new_tab_handle]
            if tab_session.user_agent:
                self.driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{tab_session.user_agent}'}});")
            
            # Navigate ke URL jika provided
            if url:
                self.visit_url_in_tab(new_tab_handle, url)
            
            self.driver.switch_to.window(original_window)
            logger.info(f"📑 Opened new tab {new_tab_handle}")
            return new_tab_handle
            
        except Exception as e:
            logger.error(f"❌ Failed to open new tab: {e}")
            return None

    def visit_url_in_tab(self, tab_id, url):
        """Kunjungi URL dalam tab tertentu"""
        try:
            if tab_id in self.driver.window_handles:
                self.driver.switch_to.window(tab_id)
                self.driver.get(url)
                
                if tab_id in self.tabs:
                    self.tabs[tab_id].stats['current_url'] = url
                    self.tabs[tab_id].stats['pages_visited'] += 1
                    self.tabs[tab_id].stats['status'] = 'Browsing'
                    self.session_data['total_pages_visited'] += 1
                
                logger.info(f"🌐 Tab {tab_id} visiting: {url}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Tab {tab_id} failed to visit {url}: {e}")
            if tab_id in self.tabs:
                self.tabs[tab_id].stats['status'] = 'Error'
        return False

    def smart_scroll_in_tab(self, tab_id, direction="down"):
        """Scroll dalam tab tertentu"""
        if tab_id not in self.tabs:
            return False
            
        duration = random.uniform(5, 12) if direction == "down" else random.uniform(3, 8)
        self.tabs[tab_id].stats['status'] = f'Scrolling {direction}'
        
        try:
            self.driver.switch_to.window(tab_id)
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            start_time = time.time()
            scroll_pause_time = 0.1
            
            if direction == "down":
                current_position = 0
                while current_position < scroll_height and (time.time() - start_time) < duration:
                    current_position += random.randint(100, 300)
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(scroll_pause_time)
            else:
                current_position = scroll_height
                while current_position > 0 and (time.time() - start_time) < duration:
                    current_position -= random.randint(100, 300)
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(scroll_pause_time)
            
            self.tabs[tab_id].stats['status'] = 'Active'
            return True
            
        except Exception as e:
            logger.warning(f"Scroll in tab {tab_id} interrupted: {e}")
            return False

    def handle_ads_in_tab(self, tab_id):
        """Handle iklan dalam tab tertentu"""
        if tab_id not in self.tabs:
            return False
            
        try:
            self.driver.switch_to.window(tab_id)
            
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
                            self.tabs[tab_id].stats['ads_closed'] += 1
                            self.session_data['total_ads_closed'] += 1
                            logger.info(f"✅ Tab {tab_id} closed ad")
                            time.sleep(1)
                            return True
                except:
                    continue
            
            close_texts = ['close', 'skip', 'tutup', 'lanjut', 'lewati']
            for text in close_texts:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            self.tabs[tab_id].stats['ads_closed'] += 1
                            self.session_data['total_ads_closed'] += 1
                            logger.info(f"✅ Tab {tab_id} closed ad with text: {text}")
                            time.sleep(1)
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Ad handling in tab {tab_id} failed: {e}")
            return False

    def click_random_links_in_tab(self, tab_id):
        """Click link acak dalam tab"""
        if tab_id not in self.tabs:
            return False
            
        try:
            self.driver.switch_to.window(tab_id)
            links = self.driver.find_elements(By.TAG_NAME, "a")
            valid_links = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and href.startswith('http') and link.is_displayed():
                        valid_links.append(link)
                except:
                    continue
            
            if valid_links:
                chosen = random.choice(valid_links[:10])
                href = chosen.get_attribute('href')
                logger.info(f"🔗 Tab {tab_id} clicking: {href[:80]}...")
                chosen.click()
                
                self.tabs[tab_id].stats['current_url'] = href
                self.tabs[tab_id].stats['pages_visited'] += 1
                self.session_data['total_pages_visited'] += 1
                
                time.sleep(random.uniform(3, 7))
                return True
                
        except Exception as e:
            logger.warning(f"Tab {tab_id} link clicking failed: {e}")
            
        return False

    def refresh_tab(self, tab_id):
        """Refresh tab tertentu"""
        try:
            self.driver.switch_to.window(tab_id)
            self.driver.refresh()
            time.sleep(2)
            self.tabs[tab_id].stats['status'] = 'Refreshed'
            return True
        except Exception as e:
            logger.error(f"Refresh tab {tab_id} failed: {e}")
            return False

    def clear_tab_data(self, tab_id):
        """Clear data dalam tab tertentu"""
        try:
            self.driver.switch_to.window(tab_id)
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            self.tabs[tab_id].stats['status'] = 'Cleaned'
        except Exception as e:
            logger.warning(f"Tab {tab_id} data clearing failed: {e}")

    def get_session_stats(self):
        """Dapatkan statistik lengkap session"""
        tab_stats = {}
        for tab_id, tab_session in self.tabs.items():
            tab_stats[str(tab_id)] = {
                'user_agent': tab_session.user_agent,
                'proxy_provider': tab_session.stats['proxy_provider'],
                'proxy_country': tab_session.stats['proxy_country'],
                'use_vpn': tab_session.use_vpn,
                'pages_visited': tab_session.stats['pages_visited'],
                'ads_closed': tab_session.stats['ads_closed'],
                'current_url': tab_session.stats['current_url'],
                'status': tab_session.stats['status'],
                'start_time': tab_session.stats['start_time']
            }
        
        return {
            'session_start': self.session_data['session_start'],
            'total_pages_visited': self.session_data['total_pages_visited'],
            'total_ads_closed': self.session_data['total_ads_closed'],
            'active_tabs': len(self.tabs),
            'current_step': self.session_data['current_step'],
            'mode': self.session_data['mode'],
            'tabs': tab_stats,
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Running'
        }

    def run_bot_session(self, target_urls):
        """Jalankan session bot"""
        self.session_data['session_start'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.setup_driver():
            logger.error("❌ Cannot start bot - driver setup failed")
            return
        
        logger.info(f"🚀 Starting bot session - Mode: {self.config['mode']}")
        
        # Buat tab utama
        main_tab = self.driver.current_window_handle
        self.create_tab_session(main_tab)
        
        # Buat tab tambahan
        for i in range(self.config['num_tabs'] - 1):
            self.open_new_tab()
        
        session_count = 0
        while True:
            try:
                session_count += 1
                self.session_data['current_step'] = f"Session #{session_count}"
                logger.info(f"🔄 Starting session #{session_count}")
                
                # Process setiap tab
                for tab_id in list(self.tabs.keys()):
                    if tab_id not in self.driver.window_handles:
                        continue
                        
                    try:
                        # Pilih URL acak
                        url = random.choice(target_urls)
                        
                        # Kunjungi URL
                        self.visit_url_in_tab(tab_id, url)
                        time.sleep(random.uniform(3, 6))
                        
                        # Handle ads
                        self.handle_ads_in_tab(tab_id)
                        
                        # Scroll down
                        self.smart_scroll_in_tab(tab_id, "down")
                        
                        # Scroll up
                        self.smart_scroll_in_tab(tab_id, "up")
                        
                        # Click random links
                        if random.random() > 0.3:
                            self.click_random_links_in_tab(tab_id)
                        
                        # Handle ads lagi
                        self.handle_ads_in_tab(tab_id)
                        
                        # Refresh
                        self.refresh_tab(tab_id)
                        
                        # Clear data
                        if random.random() > 0.5:
                            self.clear_tab_data(tab_id)
                            
                    except Exception as e:
                        logger.error(f"💥 Tab {tab_id} error: {e}")
                        continue
                
                # Tunggu sebelum session berikutnya
                wait_time = random.uniform(45, 120)
                self.session_data['current_step'] = f"Waiting {wait_time:.1f}s"
                logger.info(f"⏰ Waiting {wait_time:.1f}s before next session...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"💥 Session error: {e}")
                time.sleep(30)

class BotManager:
    def __init__(self):
        self.bot_instance = None
        self.config = {
            'mode': 'direct',
            'num_tabs': 1,
            'random_user_agent': True,
            'auto_rotate': True,
            'custom_proxies': []
        }
    
    def update_config(self, new_config):
        """Update configuration"""
        self.config.update(new_config)
        
        # Process custom proxies
        if new_config.get('custom_proxies_text'):
            self.config['custom_proxies'] = self.parse_custom_proxies(new_config['custom_proxies_text'])
        
        logger.info(f"🔄 Updated config: Mode={self.config['mode']}, Tabs={self.config['num_tabs']}")
    
    def parse_custom_proxies(self, proxies_text):
        """Parse custom proxies dari text input"""
        custom_proxies = []
        lines = proxies_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and ('http://' in line or 'https://' in line):
                try:
                    # Extract provider from URL atau gunakan custom
                    provider = "Custom"
                    if 'brightdata' in line.lower():
                        provider = "BrightData"
                    elif 'oxylabs' in line.lower():
                        provider = "Oxylabs"
                    elif 'smartproxy' in line.lower():
                        provider = "SmartProxy"
                    
                    proxy = {
                        'http': line,
                        'https': line.replace('http://', 'https://') if line.startswith('http://') else line,
                        'provider': provider,
                        'country': 'Custom'
                    }
                    custom_proxies.append(proxy)
                except Exception as e:
                    logger.warning(f"Failed to parse proxy line: {line} - {e}")
        
        logger.info(f"📝 Parsed {len(custom_proxies)} custom proxies")
        return custom_proxies
    
    def start_bot(self, target_urls):
        """Start bot dengan config saat ini"""
        if self.bot_instance:
            self.stop_bot()
            
        self.bot_instance = AdvancedSeleniumBot(self.config)
        
        def run_bot():
            self.bot_instance.run_bot_session(target_urls)
        
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        return True
    
    def stop_bot(self):
        """Stop bot"""
        if self.bot_instance and self.bot_instance.driver:
            self.bot_instance.driver.quit()
            self.bot_instance = None
            logger.info("🛑 Bot stopped")
            return True
        return False
    
    def get_stats(self):
        """Get bot statistics"""
        if self.bot_instance:
            return self.bot_instance.get_session_stats()
        return {'status': 'Stopped', 'active_tabs': 0}

# Flask Routes
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    global bot_manager
    if bot_manager:
        return jsonify(bot_manager.get_stats())
    return jsonify({'status': 'Stopped', 'active_tabs': 0})

@app.route('/api/control/start', methods=['POST'])
def control_bot_start():
    global bot_manager
    if not bot_manager:
        bot_manager = BotManager()
    
    config = request.json.get('config', {})
    bot_manager.update_config(config)
    
    # ⚠️ GANTI URL TARGET ANDA DI SINI ⚠️
    target_urls = [
        "https://cryptoajah.blogspot.com/",
        "https://cryptoajah.blogspot.com/2025/10/pengantar-cryptocurrency-apa-itu.html",
        "https://cryptoajah.blogspot.com/2025/10/memahami-dompet-digital-dan-keamanan.html",
        "https://cryptoajah.blogspot.com/",
        "https://cryptoajah.blogspot.com/2025/10/sejarah-bitcoin-dan-perkembangannya.html"
    ]
    
    if bot_manager.start_bot(target_urls):
        return jsonify({'status': 'Bot started successfully'})
    else:
        return jsonify({'status': 'Failed to start bot'})

@app.route('/api/control/stop')
def control_bot_stop():
    global bot_manager
    if bot_manager:
        bot_manager.stop_bot()
        return jsonify({'status': 'Bot stopped successfully'})
    return jsonify({'status': 'Bot not running'})

@app.route('/api/proxy/test', methods=['POST'])
def test_proxy():
    """Test koneksi proxy"""
    try:
        proxy_config = request.json.get('proxy', {})
        proxy_manager = ProxyManager()
        
        success, message = proxy_manager.test_proxy_connection(proxy_config)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Proxy test failed: {str(e)}'
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
