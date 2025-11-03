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
import json

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
            # Download VPN extension jika belum ada
            self.download_vpn_extension()
            crx_path = "touchvpn.crx"
            if os.path.exists(crx_path) and os.path.getsize(crx_path) > 1000:
                chrome_options.add_extension(crx_path)
                self.session_data['vpn_extension'] = 'Touch VPN'
                logger.info("✅ VPN Extension: Touch VPN loaded")
        except Exception as e:
            logger.warning(f"⚠️ VPN Extension: {e}")

        # 3. Konfigurasi Chrome untuk Render
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Gunakan Chrome dari instalasi manual
        chrome_options.binary_location = self.find_chrome_binary()
        
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

    def find_chrome_binary(self):
        """Cari Chrome binary"""
        paths = [
            '/tmp/chrome/chrome',
            '/tmp/chrome/google-chrome',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser'
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def download_vpn_extension(self):
        """Download VPN extension dari Chrome Web Store"""
        crx_path = "touchvpn.crx"
        if not os.path.exists(crx_path):
            vpn_url = "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=109.0&x=id%3Dbihmplhobchoageeokmgbdihknkjbknd%26installsource%3Dwebstore%26uc"
            response = requests.get(vpn_url, stream=True)
            with open(crx_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("✅ VPN extension downloaded")

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
        """4. Rubah titik Google sesuai lokasi VPN"""
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
        """5. Cek kebocoran data"""
        self.session_data['current_step'] = "Checking data leak"
        logger.info("🔍 Checking data leak...")
        
        try:
            self.driver.get("https://ipleak.net")
            time.sleep(5)
            
            # Cari informasi IP
            ip_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'IP address')]")
            if ip_elements:
                ip_info = ip_elements[0].text[:100]  # Ambil sebagian teks
                logger.info(f"📊 IP Check: {ip_info}")
            
            self.session_data['data_leak_checked'] = True
            return True
        except Exception as e:
            logger.error(f"❌ Data leak check failed: {e}")
            return False

    def visit_target_url(self, url):
        """6. Buka link target"""
        self.session_data['current_step'] = f"Visiting {url}"
        logger.info(f"🌐 Visiting target URL: {url}")
        
        try:
            self.driver.get(url)
            self.session_data['pages_visited'] += 1
            
            # Tunggu page load
            time.sleep(random.uniform(3, 6))
            return True
        except Exception as e:
            logger.error(f"❌ Failed to visit {url}: {e}")
            return False

    def smart_scroll(self, direction="down"):
        """7. Scroll dengan durasi acak setiap session"""
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
        """8. Buka link postingan acak"""
        self.session_data['current_step'] = "Clicking random post"
        logger.info("🔗 Looking for posts to click...")
        
        try:
            # Cari link yang mungkin postingan
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
            
            # Filter valid links
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
                
                # Tunggu page load
                time.sleep(random.uniform(4, 8))
                return True
            else:
                logger.warning("No posts found to click")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to click post: {e}")
            return False

    def handle_ads(self):
        """9. Lewati iklan dengan berbagai keyword"""
        self.session_data['current_step'] = "Handling ads"
        
        close_selectors = [
            "button[aria-label*='close' i]",
            "button[class*='close' i]",
            "div[class*='close' i]",
            "span[class*='close' i]",
            "a[class*='close' i]",
            ".close-btn",
            ".ad-close",
            ".skip-button",
            "[data-dismiss='modal']"
        ]
        
        # Coba dengan CSS selector
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
        
        # Coba dengan text content
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
        """10. Refresh halaman"""
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
        """11. Clear cache dan history"""
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
        """Ambil statistik session"""
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
        """12. Jalankan session lengkap dan ulang dari awal"""
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
                
                # 1. Rotasi User Agent (sudah di setup_driver)
                # 2. VPN Extension (sudah di setup_driver)
                
                # 3. Rubah titik Google
                self.change_google_location()
                
                # 4. Cek kebocoran data
                self.check_data_leak()
                
                # 5. Buka link target
                target_url = random.choice(target_urls)
                self.visit_target_url(target_url)
                
                # 6. Scroll down (durasi random)
                self.smart_scroll("down")
                
                # 7. Scroll up (durasi random)  
                self.smart_scroll("up")
                
                # 8. Buka postingan
                self.click_random_post()
                
                # 9. Handle iklan (multiple attempts)
                for _ in range(3):
                    self.handle_ads()
                    time.sleep(1)
                
                # 10. Refresh
                self.refresh_page()
                
                # 11. Clear cache
                self.clear_cache()
                
                # 12. Tunggu sebelum mengulang
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

# Flask Web Monitoring
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Selenium Bot Monitor</title>
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
            max-width: 1400px;
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
        .stats-grid {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-value {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            word-break: break-all;
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
            height: 400px;
            overflow-y: auto;
        }
        .log-entry {
            margin: 5px 0;
            font-size: 14px;
            line-height: 1.4;
        }
        .current-step {
            background: #fff3cd;
            padding: 15px;
            margin: 20px;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
        }
        .step-text {
            font-size: 16px;
            font-weight: bold;
  
