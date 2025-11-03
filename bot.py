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
import json
from datetime import datetime

class SeleniumBot:
    def __init__(self):
        self.setup_logging()
        self.ua = UserAgent()
        self.driver = None
        self.session_data = {
            'session_start': None,
            'user_agent': None,
            'vpn_location': None,
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
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.logger.info(f"Browser started with User Agent: {user_agent}")
    
    def install_vpn_extension(self):
        """Install VPN extension dari Chrome Web Store"""
        try:
            # Note: Anda perlu menambahkan extension VPN secara manual atau melalui CRX file
            # Contoh: chrome_options.add_extension('path/to/vpn_extension.crx')
            self.logger.info("VPN extension should be pre-installed in the browser")
        except Exception as e:
            self.logger.warning(f"Could not install VPN extension: {e}")
    
    def check_data_leak(self):
        """Cek kebocoran data IP"""
        try:
            self.driver.get("https://ipleak.net")
            time.sleep(5)
            
            # Ambil informasi IP dan lokasi
            ip_element = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Your IP address')]")
            self.logger.info(f"IP Check: {ip_element.text}")
            
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
            "https://www.google.co.uk"
        ]
        
        selected_domain = random.choice(google_domains)
        self.driver.get(selected_domain)
        self.logger.info(f"Accessed Google domain: {selected_domain}")
        time.sleep(3)
    
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
            "button:contains('tutup')",
            "button:contains('close')", 
            "button:contains('skip')",
            "button:contains('lanjut')",
            "button:contains('lewati')",
            ".close-btn",
            ".ad-close",
            ".skip-button"
        ]
        
        for selector in close_selectors:
            try:
                # Coba dengan CSS selector
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in close_buttons:
                    if button.is_displayed():
                        button.click()
                        self.session_data['ads_closed'] += 1
                        self.logger.info(f"Closed ad using selector: {selector}")
                        time.sleep(1)
                        return True
            except:
                continue
        
        # Coba dengan XPath untuk teks
        close_texts = ['tutup', 'close', 'skip', 'lanjut', 'lewati', 'skip ad']
        for text in close_texts:
            try:
                xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
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
            
            # Scroll down
            self.smart_scroll("down", random.uniform(8, 15))
            
            # Scroll up  
            self.smart_scroll("up", random.uniform(5, 12))
            
            # Cari dan klik link postingan
            self.click_random_post()
            
            # Handle iklan
            self.handle_ads()
            
            # Refresh halaman
            self.driver.refresh()
            time.sleep(3)
            
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
                "h3 a"
            ]
            
            all_links = []
            for selector in post_selectors:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                all_links.extend(links)
            
            # Filter link yang visible dan clickable
            clickable_links = [link for link in all_links if link.is_displayed() and link.is_enabled()]
            
            if clickable_links:
                chosen_link = random.choice(clickable_links)
                post_url = chosen_link.get_attribute('href')
                chosen_link.click()
                self.logger.info(f"Clicked on post: {post_url}")
                time.sleep(random.uniform(5, 10))
                
                # Handle iklan di halaman postingan
                self.handle_ads()
                
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
            'pages_visited': self.session_data['pages_visited'],
            'ads_closed': self.session_data['ads_closed'],
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Running'
        }
    
    def run_session(self, target_urls):
        """Jalankan satu sesi lengkap"""
        self.session_data['session_start'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Setup driver
            self.setup_driver()
            
            # Install VPN (dalam praktiknya, perlu setup manual)
            self.install_vpn_extension()
            
            while True:
                try:
                    # Cek kebocoran data
                    self.check_data_leak()
                    
                    # Rubah lokasi Google
                    self.change_google_location()
                    
                    # Kunjungi URL target (acak dari list)
                    target_url = random.choice(target_urls)
                    self.visit_target_url(target_url)
                    
                    # Clear cache
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

# Untuk monitoring web
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
        # Start bot in separate thread
        def run_bot():
            global bot_instance
            bot_instance = SeleniumBot()
            target_urls = [
                "https://www.example.com",  # Ganti dengan URL target
                "https://www.example2.com"
            ]
            bot_instance.run_session(target_urls)
        
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'Bot started'})
    elif action == 'stop' and bot_instance:
        # Implement stop logic
        return jsonify({'status': 'Stop command sent'})
    else:
        return jsonify({'status': 'Invalid action'})

if __name__ == "__main__":
    # Jalankan server monitoring di port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
