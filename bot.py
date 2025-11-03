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
            }
        }
    
    def download_crx_file(self, url, output_path):
        """Download CRX file dari URL"""
        try:
            response = requests.get(url, stream=True, timeout=30)
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
                success = self.download_crx_file(info['crx_url'], crx_path)
                if not success:
                    # Jika download gagal, buat file kosong untuk avoid error
                    open(crx_path, 'a').close()
    
    def get_random_vpn_crx(self):
        """Dapatkan path CRX acak"""
        self.download_all_extensions()
        available_vpns = []
        for name, info in self.vpn_extensions.items():
            crx_path = f"extensions/{info['crx_file']}"
            if os.path.exists(crx_path) and os.path.getsize(crx_path) > 0:
                available_vpns.append((crx_path, name))
        
        return random.choice(available_vpns) if available_vpns else (None, None)

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
            'ads_closed': 0,
            'data_leak_checked': False
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
        
        # Load VPN extension (coba di semua environment)
        try:
            crx_path, vpn_name = self.vpn_manager.get_random_vpn_crx()
            if crx_path and os.path.getsize(crx_path) > 0:
                chrome_options.add_extension(crx_path)
                self.session_data['vpn_extension'] = vpn_name
                self.logger.info(f"Loaded VPN extension: {vpn_name}")
        except Exception as e:
            self.logger.warning(f"Could not load VPN extension: {e}")
        
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
        time.sleep(3)
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
    
    def check_data_leak(self):
        """Cek kebocoran data IP"""
        try:
            self.driver.get("https://ipleak.net")
            time.sleep(5)
            
            # Ambil informasi IP
            ip_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'IP address')]")
            if ip_elements:
                self.logger.info(f"IP Check: {ip_elements[0].text}")
            self.session_data['data_leak_checked'] = True
            return True
        except Exception as e:
            self.logger.error(f"Data leak check failed: {e}")
            return False
    
    def change_google_location(self):
        """Rubah titik Google sesuai lokasi VPN"""
        google_domains = [
            "https://www.google.com",
            "https://www.google.co.id", 
            "https://www.google.com.sg",
            "https://www.google.com.my",
            "https://www.google.com.au",
            "https://www.google.co.jp",
            "https://www.google.co.uk",
            "https://www.google.de",
            "https://www.google.fr"
        ]
        
        selected_domain = random.choice(google_domains)
        try:
            self.driver.get(selected_domain)
            time.sleep(3)
            self.logger.info(f"Accessed Google domain: {selected_domain}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to access {selected_domain}: {e}")
            return False
    
    def smart_scroll(self, direction="down", duration=None):
        """Scroll halaman dengan durasi acak"""
        if duration is None:
            duration = random.uniform(5, 15)
        
        self.logger.info(f"Scrolling {direction} for {duration:.2f} seconds")
        
        start_time = time.time()
        scroll_pause_time = 0.1
        
        if direction == "down":
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            while current_position < scroll_height and (time.time() - start_time) < duration:
                current_position += random.randint(50, 200)
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(scroll_pause_time)
        else:  # up
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = scroll_height
            while current_position > 0 and (time.time() - start_time) < duration:
                current_position -= random.randint(50, 200)
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(scroll_pause_time)
    
    def handle_ads(self):
        """Coba tutup iklan dengan berbagai selector"""
        close_selectors = [
            "button[aria-label*='close' i]",
            "button[class*='close' i]",
            "div[class*='close' i]",
            "span[class*='close' i]",
            "a[class*='close' i]",
            ".close-btn",
            ".ad-close",
            ".skip-button",
            "[data-dismiss='modal']",
            ".modal-close"
        ]
        
        for selector in close_selectors:
            try:
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in close_buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        self.session_data['ads_closed'] += 1
                        self.logger.info(f"Closed ad using selector: {selector}")
                        time.sleep(1)
                        return True
            except:
                continue
        
        # Coba dengan XPath untuk teks
        close_texts = ['tutup', 'close', 'skip', 'lanjut', 'lewati', 'skip ad', 'tutup iklan']
        for text in close_texts:
            try:
                xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        self.session_data['ads_closed'] += 1
                        self.logger.info(f"Closed ad with text: {text}")
                        time.sleep(1)
                        return True
            except:
                continue
        
        return False
    
    def visit_target_url(self, url):
        """Kunjungi URL target dengan berbagai interaksi"""
        try:
            self.driver.get(url)
            self.session_data['pages_visited'] += 1
            self.logger.info(f"Visited target URL: {url}")
            
            # Tunggu halaman load
            time.sleep(random.uniform(3, 7))
            
            # Handle initial ads
            self.handle_ads()
            
            # Scroll down
            self.smart_scroll("down", random.uniform(8, 15))
            
            # Scroll up  
            self.smart_scroll("up", random.uniform(5, 12))
            
            # Cari dan klik link postingan
            if self.click_random_post():
                # Jika berhasil klik post, handle ads lagi
                self.handle_ads()
            
            # Refresh halaman
            self.driver.refresh()
            time.sleep(3)
            
            # Handle ads setelah refresh
            self.handle_ads()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error visiting URL {url}: {e}")
            return False
    
    def click_random_post(self):
        """Klik postingan acak di halaman"""
        try:
            # Cari semua link yang mungkin merupakan postingan
            post_selectors = [
                "a[href*='post']",
                "a[href*='article']", 
                "a[href*='blog']",
                "a[class*='post']",
                "a[class*='article']",
                ".post-title a",
                ".entry-title a",
                "h2 a",
                "h3 a",
                ".title a",
                "[class*='title'] a"
            ]
            
            all_links = []
            for selector in post_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_links.extend(links)
                except:
                    continue
            
            # Filter link yang visible dan clickable
            clickable_links = []
            for link in all_links:
                try:
                    if link.is_displayed() and link.is_enabled():
                        clickable_links.append(link)
                except:
                    continue
            
            if clickable_links:
                chosen_link = random.choice(clickable_links)
                post_url = chosen_link.get_attribute('href') or "No URL"
                chosen_link.click()
                self.logger.info(f"Clicked on post: {post_url}")
                time.sleep(random.uniform(5, 10))
                return True
                
        except Exception as e:
            self.logger.warning(f"Could not click random post: {e}")
        
        return False
    
    def clear_cache(self):
        """Clear cache dan history"""
        try:
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            self.driver.delete_all_cookies()
            self.logger.info("Cache and cookies cleared")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    def get_session_stats(self):
        """Dapatkan statistik sesi"""
        return {
            'session_start': self.session_data['session_start'],
            'user_agent': self.session_data['user_agent'],
            'vpn_extension': self.session_data['vpn_extension'],
            'pages_visited': self.session_data['pages_visited'],
            'ads_closed': self.session_data['ads_closed'],
            'data_leak_checked': self.session_data['data_leak_checked'],
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Running'
        }
    
    def run_session(self, target_urls):
        """Jalankan satu sesi lengkap"""
        self.session_data['session_start'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Setup driver
            self.setup_driver()
            
            while True:
                try:
                    # Step 1: Cek kebocoran data
                    self.logger.info("Step 1: Checking data leak...")
                    self.check_data_leak()
                    
                    # Step 2: Rubah lokasi Google
                    self.logger.info("Step 2: Changing Google location...")
                    self.change_google_location()
                    
                    # Step 3: Kunjungi URL target (acak dari list)
                    target_url = random.choice(target_urls)
                    self.logger.info(f"Step 3: Visiting target URL: {target_url}")
                    self.visit_target_url(target_url)
                    
                    # Step 4: Clear cache
                    self.logger.info("Step 4: Clearing cache...")
                    self.clear_cache()
                    
                    # Tunggu sebelum sesi berikutnya
                    wait_time = random.uniform(30, 120)
                    self.logger.info(f"Waiting {wait_time:.2f} seconds before next session...")
                    time.sleep(wait_time)
                    
                except KeyboardInterrupt:
                    self.logger.info("Bot stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in session: {e}")
                    time.sleep(30)  # Tunggu sebelum retry
                    
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")

# Flask app
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
            # GANTI DENGAN URL TARGET ANDA
            target_urls = [
                "https://www.example.com",
                "https://www.example2.com"
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
