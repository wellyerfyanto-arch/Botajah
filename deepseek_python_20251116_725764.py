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
import requests

app = Flask(__name__)

# Global variables
automation_thread = None
is_running = False
session_stats = {
    'sessions_completed': 0,
    'tabs_opened': 0,
    'ads_clicked': 0,
    'pages_visited': 0,
    'proxy_changes': 0,
    'current_proxy': 'Direct',
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

# Default Free Proxies (fallback)
DEFAULT_FREE_PROXIES = [
    "103.155.62.158:8080",
    "103.174.45.58:8080", 
    "103.175.237.9:3128",
    "103.176.96.100:8080",
    "103.178.43.18:8181",
    "103.179.187.6:8080",
    "103.181.45.9:8080",
    "103.189.234.105:80",
    "103.194.242.254:8080",
    "103.197.251.202:80",
]

class ProxyManager:
    def __init__(self):
        self.current_proxy = None
        self.free_proxies = DEFAULT_FREE_PROXIES.copy()
        self.premium_proxies = []
    
    def set_free_proxies(self, proxy_list):
        """Set free proxies from user input"""
        if proxy_list:
            self.free_proxies = [proxy.strip() for proxy in proxy_list if proxy.strip()]
            stream_logger.log(f"Loaded {len(self.free_proxies)} free proxies from input", 'info')
        else:
            self.free_proxies = DEFAULT_FREE_PROXIES.copy()
            stream_logger.log("Using default free proxies", 'info')
    
    def set_premium_proxy(self, proxy_url):
        """Set premium proxy from user input"""
        if proxy_url and proxy_url.strip():
            self.premium_proxies = [proxy_url.strip()]
            stream_logger.log("Premium proxy set from input", 'info')
            return True
        return False
    
    def get_random_free_proxy(self):
        """Get random free proxy from list"""
        if not self.free_proxies:
            return None
        
        # Format proxy URL
        proxy = random.choice(self.free_proxies)
        if not proxy.startswith('http'):
            proxy = f"http://{proxy}"
        return proxy
    
    def get_premium_proxy(self):
        """Get premium proxy"""
        if not self.premium_proxies:
            return None
        return self.premium_proxies[0]
    
    def validate_proxy(self, proxy_url):
        """Test if proxy is working"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                stream_logger.log(f"Proxy validated: {proxy_url}", 'info')
                return True
        except Exception as e:
            stream_logger.log(f"Proxy validation failed for {proxy_url}: {str(e)}", 'warning')
        return False
    
    def rotate_proxy(self, proxy_type='free', custom_proxy=None):
        """Rotate to new proxy"""
        old_proxy = self.current_proxy
        
        if proxy_type == 'premium':
            premium_proxy = self.get_premium_proxy() or custom_proxy
            if premium_proxy and self.validate_proxy(premium_proxy):
                self.current_proxy = premium_proxy
                stream_logger.log(f"Using premium proxy: {premium_proxy}", 'success')
                return True
            else:
                stream_logger.log("Premium proxy validation failed, falling back to free proxy", 'warning')
                proxy_type = 'free'
        
        if proxy_type == 'free':
            # Try up to 5 random free proxies
            tested_proxies = set()
            for attempt in range(5):
                if len(tested_proxies) >= len(self.free_proxies):
                    break
                    
                new_proxy = self.get_random_free_proxy()
                while new_proxy in tested_proxies:
                    new_proxy = self.get_random_free_proxy()
                
                tested_proxies.add(new_proxy)
                
                if new_proxy and self.validate_proxy(new_proxy):
                    self.current_proxy = new_proxy
                    stream_logger.log(f"Using free proxy: {new_proxy}", 'success')
                    return True
            
            # If no free proxy works, use direct connection
            stream_logger.log("No working free proxies found, using direct connection", 'warning')
            self.current_proxy = None
            return False
        
        return False
    
    def get_current_proxy_display(self):
        """Get display-friendly proxy info"""
        if not self.current_proxy:
            return "Direct Connection"
        
        if "username" in self.current_proxy or "@" in self.current_proxy:
            return "Premium Proxy (Active)"
        
        # Extract IP for display
        try:
            proxy_parts = self.current_proxy.split('//')
            if len(proxy_parts) > 1:
                ip_port = proxy_parts[1].split(':')
                return f"Free Proxy: {ip_port[0]}"
        except:
            pass
        
        return f"Proxy: {self.current_proxy}"

# User Agents
DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
]

MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]

def get_random_user_agent(device_type='random'):
    if device_type == 'desktop':
        return random.choice(DESKTOP_USER_AGENTS)
    elif device_type == 'mobile':
        return random.choice(MOBILE_USER_AGENTS)
    else:
        return random.choice(DESKTOP_USER_AGENTS + MOBILE_USER_AGENTS)

class BrowserAutomation:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.proxy_manager = ProxyManager()
        
        # Setup proxies from config
        self.setup_proxies()
        
    def setup_proxies(self):
        """Setup proxies from configuration"""
        proxy_config = self.config.get('proxy_config', 'none')
        
        if proxy_config == 'free':
            free_proxies_input = self.config.get('free_proxies', [])
            self.proxy_manager.set_free_proxies(free_proxies_input)
        elif proxy_config == 'premium':
            premium_proxy = self.config.get('premium_proxy', '')
            self.proxy_manager.set_premium_proxy(premium_proxy)
    
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
            
            # Performance optimizations
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            
            # Set user agent
            device_type = self.config.get('device_type', 'random')
            user_agent = get_random_user_agent(device_type)
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Setup proxy based on configuration
            proxy_config = self.config.get('proxy_config', 'none')
            
            if proxy_config != 'none':
                success = self.proxy_manager.rotate_proxy(proxy_type=proxy_config)
                
                if success and self.proxy_manager.current_proxy:
                    chrome_options.add_argument(f'--proxy-server={self.proxy_manager.current_proxy}')
                    stream_logger.log(f"Proxy configured: {self.proxy_manager.current_proxy}", 'info')
                else:
                    stream_logger.log("No proxy configured, using direct connection", 'info')
            
            # Update session stats with proxy info
            session_stats['current_proxy'] = self.proxy_manager.get_current_proxy_display()
            stream_logger.update_stats(session_stats)
            
            stream_logger.log(f"Browser setup - Proxy: {session_stats['current_proxy']}, User Agent: {user_agent[:50]}...", 'info')
            
            # Initialize driver
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
            
        except Exception as e:
            stream_logger.log(f"Driver setup failed: {str(e)}", 'error')
            return False
    
    def rotate_proxy_if_needed(self):
        """Rotate proxy based on configuration"""
        proxy_config = self.config.get('proxy_config', 'none')
        
        # Rotate proxy with 40% chance for free proxies, 10% for premium
        rotate_chance = 0.4 if proxy_config == 'free' else 0.1 if proxy_config == 'premium' else 0
        
        if random.random() < rotate_chance:
            old_proxy = self.proxy_manager.get_current_proxy_display()
            
            success = self.proxy_manager.rotate_proxy(proxy_type=proxy_config)
            
            if success:
                session_stats['proxy_changes'] += 1
                session_stats['current_proxy'] = self.proxy_manager.get_current_proxy_display()
                stream_logger.update_stats(session_stats)
                stream_logger.log(f"Proxy rotated: {old_proxy} -> {session_stats['current_proxy']}", 'info')
                
                # Restart browser with new proxy
                if self.driver:
                    self.driver.quit()
                return self.setup_driver()
        
        return True
    
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
                random_result = random.choice(results[1:min(6, len(results))])
                random_result.click()
                self.human_like_delay(3, 6)
                return True
            return False
            
        except Exception as e:
            stream_logger.log(f"Click random result failed: {str(e)}", 'error')
            return False
    
    def visit_url(self, url):
        """Visit a URL directly"""
        try:
            self.driver.get(url)
            self.human_like_delay(3, 6)
            self.human_scroll(random.randint(2, 4))
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
            
            stream_logger.log(f"Session {session_num} started with {session_stats['current_proxy']}", 'info')
            
            # Perform activities for each query/URL
            for i, item in enumerate(search_queries):
                if not is_running:
                    break
                
                stream_logger.log(f"Session {session_num}, Activity {i+1}: Processing '{item}'", 'info')
                
                # Rotate proxy if needed (after every 2 activities for free proxies)
                if i > 0 and i % 2 == 0:
                    if not self.rotate_proxy_if_needed():
                        stream_logger.log("Proxy rotation failed, continuing with current setup", 'warning')
                
                if item.startswith('http'):
                    # Direct URL visit
                    success = self.visit_url(item)
                else:
                    # Google search
                    success = self.google_search(item)
                    if success:
                        self.human_scroll(random.randint(2, 4))
                        
                        # Click random result
                        if self.click_random_result():
                            self.human_like_delay(10, 20)
                            self.human_scroll(2)
                
                if success:
                    session_stats['pages_visited'] += 1
                    session_stats['tabs_opened'] += 1
                    stream_logger.update_stats(session_stats)
                
                # Wait between activities
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

# Flask Routes
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
        'proxy_changes': 0,
        'current_proxy': 'Not set',
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

@app.route('/proxy/rotate', methods=['POST'])
def rotate_proxy():
    """Manual proxy rotation endpoint"""
    config = request.json
    proxy_manager = ProxyManager()
    
    # Setup proxies based on config
    if config.get('proxy_config') == 'free':
        proxy_manager.set_free_proxies(config.get('free_proxies', []))
    elif config.get('proxy_config') == 'premium':
        proxy_manager.set_premium_proxy(config.get('premium_proxy', ''))
    
    success = proxy_manager.rotate_proxy(proxy_type=config.get('proxy_config', 'free'))
    
    if success:
        session_stats['proxy_changes'] += 1
        session_stats['current_proxy'] = proxy_manager.get_current_proxy_display()
        stream_logger.update_stats(session_stats)
    
    return jsonify({'success': success, 'current_proxy': session_stats['current_proxy']})

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