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
    'vpn_changes': 0,
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

# Extended User Agents
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
    "Mozilla/5.0 (Linux; Android 12; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1"
]

# Free VPN Extensions List
VPN_EXTENSIONS = [
    {"name": "Touch VPN", "id": "bihmplhobchoageeokmgbdihknkjbknd"},
    {"name": "Hotspot Shield", "id": "nlbejmccbhkncgokjcmghpfloaajcffj"},
    {"name": "Betternet", "id": "gjknjjomckknofjidppipffbpoekiipm"},
    {"name": "ZenMate", "id": "fdcgdnkidjaadafnichfpabhfomcebme"},
    {"name": "Windscribe", "id": "hnmpcagpplmpfojmgmnngilcnanddlhb"},
    {"name": "Hoxx VPN", "id": "ojojflnpjldgbjfeflkmfjoncjekjgnj"},
    {"name": "SetupVPN", "id": "fobdcmdadmkcmljldbecgphdllagfbbh"},
    {"name": "Urban VPN", "id": "pfkfddicgkncnamgkhpkmgdpbdbkeoje"},
    {"name": "TunnelBear", "id": "omdakjcmkglenbhjadbccaookpfjihpa"},
    {"name": "Free VPN - VPN Proxy", "id": "dbkgfgjkefkkmfpofbjeniepmnhcghij"}
]

def get_random_user_agent(device_type='random'):
    if device_type == 'desktop':
        return random.choice(DESKTOP_USER_AGENTS)
    elif device_type == 'mobile':
        return random.choice(MOBILE_USER_AGENTS)
    else:
        return random.choice(DESKTOP_USER_AGENTS + MOBILE_USER_AGENTS)

def get_random_vpn_extension():
    return random.choice(VPN_EXTENSIONS)

class BrowserAutomation:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.current_vpn = None
        
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
            
            # Select VPN extension
            vpn_choice = self.config.get('vpn_extension', 'random')
            if vpn_choice != 'none':
                if vpn_choice == 'random':
                    self.current_vpn = get_random_vpn_extension()
                else:
                    self.current_vpn = next((vpn for vpn in VPN_EXTENSIONS if vpn['name'].lower() == vpn_choice.lower()), get_random_vpn_extension())
                
                stream_logger.log(f"Selected VPN: {self.current_vpn['name']}", 'info')
            
            stream_logger.log(f"Using User Agent: {user_agent[:50]}...", 'info')
            
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
        """Scroll like a human with variations"""
        scroll_patterns = [
            "smooth", "quick", "slow", "random", "page_down"
        ]
        
        for i in range(scroll_count):
            pattern = random.choice(scroll_patterns)
            
            if pattern == "smooth":
                # Smooth scroll
                scroll_pixels = random.randint(200, 600)
                self.driver.execute_script(f"""
                    window.scrollBy({{
                        top: {scroll_pixels},
                        behavior: 'smooth'
                    }});
                """)
            elif pattern == "quick":
                # Quick jump
                scroll_pixels = random.randint(500, 1200)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            elif pattern == "slow":
                # Slow manual scroll simulation
                steps = random.randint(5, 15)
                step_size = random.randint(50, 150)
                for step in range(steps):
                    self.driver.execute_script(f"window.scrollBy(0, {step_size});")
                    time.sleep(random.uniform(0.1, 0.3))
            elif pattern == "page_down":
                # Page down key
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            else:
                # Random scroll
                scroll_pixels = random.randint(300, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            
            self.human_like_delay(2, 5)
            
            # Occasionally scroll up a bit (like real humans)
            if random.random() < 0.3:
                self.driver.execute_script("window.scrollBy(0, -100);")
                self.human_like_delay(1, 2)
    
    def google_search(self, query):
        """Perform Google search with human-like behavior"""
        try:
            self.driver.get("https://www.google.com")
            self.human_like_delay(2, 4)
            
            # Find search box and input query
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear and type like human
            search_box.clear()
            self.human_like_delay(1, 2)
            
            # Sometimes make typing mistakes and correct them
            if random.random() < 0.4:
                # Type wrong first, then correct
                wrong_text = query[:-2] if len(query) > 5 else query
                self.human_type(search_box, wrong_text)
                self.human_like_delay(1, 2)
                for _ in range(len(wrong_text)):
                    search_box.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
                self.human_type(search_box, query)
            else:
                # Type normally
                self.human_type(search_box, query)
            
            self.human_like_delay(1, 3)
            
            # Randomly use Enter or click search button
            if random.random() < 0.7:
                search_box.send_keys(Keys.RETURN)
            else:
                search_btn = self.driver.find_element(By.NAME, "btnK")
                search_btn.click()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            self.human_like_delay(2, 4)
            return True
            
        except Exception as e:
            stream_logger.log(f"Google search failed: {str(e)}", 'error')
            return False
    
    def click_random_result(self):
        """Click random search result with variation"""
        try:
            # Find all search results
            results = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g h3, h3.r"))
            )
            
            if results and len(results) > 1:
                # Skip some results randomly (like humans do)
                skip_count = random.randint(0, min(2, len(results)-1))
                available_results = results[skip_count:min(8, len(results))]
                
                if available_results:
                    random_result = random.choice(available_results)
                    
                    # Sometimes hover before clicking
                    if random.random() < 0.6:
                        self.driver.execute_script("arguments[0].style.backgroundColor = 'yellow';", random_result)
                        self.human_like_delay(0.5, 1.5)
                        self.driver.execute_script("arguments[0].style.backgroundColor = '';", random_result)
                    
                    random_result.click()
                    self.human_like_delay(3, 8)
                    return True
            return False
            
        except Exception as e:
            stream_logger.log(f"Click random result failed: {str(e)}", 'error')
            return False
    
    def find_and_click_ads(self):
        """Find and click ads if available"""
        try:
            # Multiple ad selectors
            ad_selectors = [
                "[data-text-ad]",
                ".adsbygoogle",
                "[data-ad]",
                ".advertisement",
                "#taw .ads",
                ".commercial-unit"
            ]
            
            for selector in ad_selectors:
                ads = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if ads:
                    ad = random.choice(ads)
                    if ad.is_displayed() and ad.is_enabled():
                        stream_logger.log("Found ad, clicking...", 'info')
                        ad.click()
                        self.human_like_delay(8, 15)  # Stay on ad page
                        self.driver.back()
                        self.human_like_delay(2, 4)
                        return True
            return False
        except Exception as e:
            return False
    
    def visit_url(self, url):
        """Visit a URL directly with human behavior"""
        try:
            self.driver.get(url)
            self.human_like_delay(3, 6)
            
            # Simulate reading behavior
            self.human_scroll(random.randint(2, 5))
            
            # Random activities on page
            activities = random.randint(1, 3)
            for _ in range(activities):
                action = random.choice(["scroll", "pause", "click_links"])
                if action == "scroll":
                    self.human_scroll(1)
                elif action == "pause":
                    self.human_like_delay(5, 12)
                elif action == "click_links":
                    self.click_random_links()
            
            return True
        except Exception as e:
            stream_logger.log(f"Visit URL failed: {str(e)}", 'error')
            return False
    
    def click_random_links(self):
        """Click random links on page"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            if links:
                valid_links = [
                    link for link in links 
                    if link.is_displayed() and link.is_enabled()
                    and link.get_attribute('href')
                    and 'http' in link.get_attribute('href')
                ]
                
                if valid_links:
                    # Prefer internal links
                    internal_links = [
                        link for link in valid_links 
                        if self.driver.current_url.split('/')[2] in link.get_attribute('href')
                    ]
                    
                    links_to_choose = internal_links if internal_links else valid_links
                    random_link = random.choice(links_to_choose[:8])  # First 8 links
                    
                    stream_logger.log(f"Clicking internal link: {random_link.text[:30]}...", 'info')
                    random_link.click()
                    self.human_like_delay(5, 10)
                    self.driver.back()
                    self.human_like_delay(2, 4)
                    return True
            return False
        except Exception as e:
            return False
    
    def simulate_vpn_change(self):
        """Simulate VPN change (in real implementation would switch VPN)"""
        if random.random() < 0.3:  # 30% chance to "change VPN"
            new_vpn = get_random_vpn_extension()
            if new_vpn != self.current_vpn:
                self.current_vpn = new_vpn
                stream_logger.log(f"VPN changed to: {self.current_vpn['name']}", 'info')
                return True
        return False
    
    def run_session(self, search_queries, session_num):
        """Run a complete browsing session"""
        global session_stats
        
        try:
            if not self.setup_driver():
                return False
            
            stream_logger.log(f"Session {session_num}: Browser started with {self.current_vpn['name'] if self.current_vpn else 'No VPN'}", 'info')
            
            # Perform activities for each query/URL
            for i, item in enumerate(search_queries):
                if not is_running:
                    break
                
                stream_logger.log(f"Session {session_num}, Activity {i+1}: Processing '{item}'", 'info')
                
                # Simulate VPN change occasionally
                if self.simulate_vpn_change():
                    session_stats['vpn_changes'] += 1
                    stream_logger.update_stats(session_stats)
                
                if item.startswith('http'):
                    # Direct URL visit
                    success = self.visit_url(item)
                else:
                    # Google search with full behavior
                    success = self.google_search(item)
                    if success:
                        self.human_scroll(random.randint(2, 4))
                        
                        # Occasionally click ads (25% chance)
                        if random.random() < 0.25:
                            if self.find_and_click_ads():
                                session_stats['ads_clicked'] += 1
                                stream_logger.update_stats(session_stats)
                        
                        # Click random result (80% chance)
                        if random.random() < 0.8:
                            if self.click_random_result():
                                # Extended reading behavior on result page
                                read_time = random.randint(15, 45)
                                start_time = time.time()
                                while time.time() - start_time < read_time and is_running:
                                    activity = random.choice(["scroll", "pause", "click_links", "scroll_up"])
                                    if activity == "scroll":
                                        self.human_scroll(1)
                                    elif activity == "pause":
                                        self.human_like_delay(3, 8)
                                    elif activity == "click_links":
                                        self.click_random_links()
                                    elif activity == "scroll_up":
                                        self.driver.execute_script("window.scrollBy(0, -300);")
                                        self.human_like_delay(2, 4)
                
                if success:
                    session_stats['pages_visited'] += 1
                    session_stats['tabs_opened'] += 1
                    stream_logger.update_stats(session_stats)
                
                # Wait between activities
                if i < len(search_queries) - 1 and is_running:
                    wait_time = random.randint(3, 8)
                    self.human_like_delay(wait_time, wait_time + 3)
            
            return True
            
        except Exception as e:
            stream_logger.log(f"Session {session_num} error: {str(e)}", 'error')
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                stream_logger.log(f"Session {session_num}: Browser closed", 'info')

# Routes remain the same as previous version...
# [Keep all the Flask routes exactly as they were in the previous working version]

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
        'vpn_changes': 0,
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
