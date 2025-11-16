from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import json
import time
import threading
import os
import random
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Global variables
automation_thread = None
is_running = False
session_stats = {
    'sessions_completed': 0,
    'tabs_opened': 0,
    'ads_clicked': 0,
    'pages_visited': 0,
    'start_time': None
}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamLogger:
    def __init__(self):
        self.listeners = []
    
    def log(self, message, level='info'):
        log_entry = {
            'type': 'log',
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        self._emit(log_entry)
        logger.info(f"{level.upper()}: {message}")
    
    def update_stats(self, stats):
        stats_entry = {
            'type': 'stats',
            'data': stats
        }
        self._emit(stats_entry)
    
    def update_status(self, status):
        status_entry = {
            'type': 'status',
            'message': status
        }
        self._emit(status_entry)
    
    def _emit(self, data):
        for listener in self.listeners:
            try:
                listener.append(json.dumps(data) + '\n')
            except:
                self.listeners.remove(listener)

stream_logger = StreamLogger()

class BrowserAutomation:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.ua = UserAgent()
        
    def setup_driver(self):
        try:
            chrome_options = Options()
            
            # Setup for Render environment
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Headless mode for Render
            chrome_options.add_argument("--headless=new")
            
            # Anti-detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set random user agent based on device type
            device_type = self.config.get('device_type', 'random')
            if device_type == 'desktop':
                user_agent = self.ua.chrome
            elif device_type == 'mobile':
                user_agent = self.ua.random
            else:
                user_agent = random.choice([self.ua.chrome, self.ua.random])
            
            chrome_options.add_argument(f'--user-agent={user_agent}')
            stream_logger.log(f"Using User Agent: {user_agent}", 'info')
            
            # Initialize driver
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
            
        except Exception as e:
            stream_logger.log(f"Driver setup failed: {str(e)}", 'error')
            return False
    
    def human_like_delay(self, min_sec=1, max_sec=3):
        time.sleep(random.uniform(min_sec, max_sec))
    
    def human_type(self, element, text):
        """Type like a human with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
    
    def human_scroll(self, scroll_count=3):
        """Scroll like a human"""
        for i in range(scroll_count):
            scroll_type = random.choice(["smooth", "quick", "slow"])
            scroll_pixels = random.randint(300, 800)
            
            if scroll_type == "smooth":
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            elif scroll_type == "quick":
                self.driver.execute_script(f"window.scrollTo(0, {scroll_pixels});")
            else:
                current_pos = self.driver.execute_script("return window.pageYOffset;")
                target_pos = current_pos + scroll_pixels
                self.driver.execute_script(f"window.scrollTo(0, {target_pos});")
            
            self.human_like_delay(2, 4)
    
    def google_search(self, query):
        """Perform Google search"""
        try:
            self.driver.get("https://www.google.com")
            self.human_like_delay(2, 4)
            
            # Accept cookies if present
            try:
                accept_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all')]"))
                )
                accept_btn.click()
                self.human_like_delay(1, 2)
            except:
                pass
            
            # Find search box and input query
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            search_box.clear()
            self.human_type(search_box, query)
            self.human_like_delay(1, 2)
            
            search_box.send_keys(Keys.RETURN)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            self.human_like_delay(2, 4)
            return True
            
        except Exception as e:
            stream_logger.log(f"Google search failed: {str(e)}", 'error')
            return False
    
    def click_random_result(self):
        """Click random search result"""
        try:
            # Find all search results
            results = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g h3"))
            )
            
            if results and len(results) > 1:
                # Skip first result (might be ad) and choose random from rest
                random_result = random.choice(results[1:min(6, len(results))])
                random_result.click()
                self.human_like_delay(3, 6)
                return True
            return False
            
        except Exception as e:
            stream_logger.log(f"Click random result failed: {str(e)}", 'error')
            return False
    
    def click_ads_if_exist(self):
        """Click ads if available"""
        try:
            # Look for ad elements (this selector might need adjustment)
            ads = self.driver.find_elements(By.CSS_SELECTOR, "[data-text-ad]")
            if ads:
                ad = random.choice(ads)
                ad.click()
                self.human_like_delay(10, 20)  # Stay on ad page
                self.driver.back()
                self.human_like_delay(2, 4)
                return True
            return False
        except Exception as e:
            stream_logger.log(f"Click ads failed: {str(e)}", 'error')
            return False
    
    def simulate_reading_behavior(self, duration=30):
        """Simulate reading behavior"""
        start_time = time.time()
        while time.time() - start_time < duration:
            activity = random.choice(["scroll", "pause", "click_links"])
            
            if activity == "scroll":
                self.human_scroll(1)
            elif activity == "pause":
                self.human_like_delay(5, 10)
            elif activity == "click_links":
                self.click_random_links()
    
    def click_random_links(self):
        """Click random links on page"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            if links:
                valid_links = [link for link in links if link.is_displayed() and link.is_enabled()]
                if valid_links:
                    random_link = random.choice(valid_links[:10])
                    random_link.click()
                    self.human_like_delay(5, 10)
                    self.driver.back()
                    self.human_like_delay(2, 4)
        except Exception as e:
            pass
    
    def visit_url(self, url):
        """Visit a URL directly"""
        try:
            self.driver.get(url)
            self.human_like_delay(3, 6)
            self.human_scroll(random.randint(2, 4))
            self.simulate_reading_behavior(random.randint(20, 40))
            return True
        except Exception as e:
            stream_logger.log(f"Visit URL failed: {str(e)}", 'error')
            return False
    
    def run_session(self, search_queries, session_num):
        """Run a complete browsing session"""
        global session_stats
        
        try:
            if not self.setup_driver():
                return False
            
            stream_logger.log(f"Session {session_num}: Browser started successfully", 'info')
            
            # Perform activities for each query/URL
            for i, item in enumerate(search_queries):
                if not is_running:
                    break
                
                stream_logger.log(f"Session {session_num}, Tab {i+1}: Processing '{item}'", 'info')
                
                if item.startswith('http'):
                    # Direct URL visit
                    success = self.visit_url(item)
                else:
                    # Google search
                    success = self.google_search(item)
                    if success:
                        self.human_scroll(random.randint(2, 4))
                        
                        # Occasionally click ads
                        if random.random() < 0.3:
                            self.click_ads_if_exist()
                            session_stats['ads_clicked'] += 1
                        
                        # Click random result
                        if self.click_random_result():
                            self.simulate_reading_behavior(random.randint(20, 60))
                            self.click_random_links()
                            self.human_scroll(2)
                
                if success:
                    session_stats['pages_visited'] += 1
                    session_stats['tabs_opened'] += 1
                    stream_logger.update_stats(session_stats)
                
                # Wait between tabs
                if i < len(search_queries) - 1:
                    self.human_like_delay(2, 5)
            
            return True
            
        except Exception as e:
            stream_logger.log(f"Session {session_num} error: {str(e)}", 'error')
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                stream_logger.log(f"Session {session_num}: Browser closed", 'info')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_automation():
    global automation_thread, is_running, session_stats
    
    if is_running:
        return jsonify({'success': False, 'error': 'Automation is already running'})
    
    config = request.json
    stream_logger.log('Starting automation session...', 'info')
    
    # Reset stats
    session_stats = {
        'sessions_completed': 0,
        'tabs_opened': 0,
        'ads_clicked': 0,
        'pages_visited': 0,
        'start_time': datetime.now().isoformat()
    }
    
    is_running = True
    
    automation_thread = threading.Thread(
        target=run_automation_session,
        args=(config,)
    )
    automation_thread.daemon = True
    automation_thread.start()
    
    return jsonify({'success': True})

@app.route('/stop', methods=['POST'])
def stop_automation():
    global is_running
    
    if not is_running:
        return jsonify({'success': False, 'error': 'No automation running'})
    
    is_running = False
    stream_logger.log('Stopping automation...', 'info')
    stream_logger.update_status('Stopping')
    
    return jsonify({'success': True})

@app.route('/stream')
def stream():
    def generate():
        messages = []
        stream_logger.listeners.append(messages)
        try:
            while True:
                if messages:
                    message = messages.pop(0)
                    yield f"data: {message}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                    time.sleep(1)
        except GeneratorExit:
            if messages in stream_logger.listeners:
                stream_logger.listeners.remove(messages)
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/status')
def status():
    return jsonify({
        'running': is_running,
        'stats': session_stats
    })

def run_automation_session(config):
    global is_running, session_stats
    
    try:
        # Prepare search queries and URLs
        search_queries = [config.get('search_query', 'python programming')]
        custom_urls = config.get('custom_urls', [])
        
        # Combine search queries and custom URLs
        all_items = search_queries + [url.strip() for url in custom_urls if url.strip()]
        
        session_count = config.get('session_count', 1)
        tab_count = min(config.get('tab_count', 3), len(all_items))
        
        stream_logger.log(f'Starting {session_count} sessions with {tab_count} tabs each', 'info')
        stream_logger.update_status('Running')
        
        # Run sessions
        for session_num in range(session_count):
            if not is_running:
                break
                
            stream_logger.log(f'Session {session_num + 1} started', 'info')
            
            # Select random items for this session
            session_items = random.sample(all_items, min(tab_count, len(all_items)))
            
            automation = BrowserAutomation(config)
            success = automation.run_session(session_items, session_num + 1)
            
            if success:
                session_stats['sessions_completed'] += 1
                stream_logger.update_stats(session_stats)
                stream_logger.log(f'Session {session_num + 1} completed successfully', 'success')
            else:
                stream_logger.log(f'Session {session_num + 1} failed', 'error')
            
            # Wait between sessions
            if session_num < session_count - 1 and is_running:
                wait_time = random.randint(10, 30)
                stream_logger.log(f'Waiting {wait_time} seconds before next session...', 'info')
                for _ in range(wait_time):
                    if not is_running:
                        break
                    time.sleep(1)
        
        if is_running:
            stream_logger.log('All sessions completed!', 'success')
            stream_logger.update_status('Completed')
        else:
            stream_logger.log('Automation stopped by user', 'info')
            stream_logger.update_status('Stopped')
            
    except Exception as e:
        stream_logger.log(f'Automation error: {str(e)}', 'error')
        stream_logger.update_status('Error')
    
    finally:
        is_running = False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
