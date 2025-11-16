from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import json
import time
import threading
import os
import random
import subprocess
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
    'vpn_changes': 0,
    'current_ip': 'Unknown',
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

# VPN Management
class VPNManager:
    @staticmethod
    def get_current_ip():
        """Get current public IP address"""
        try:
            response = requests.get('http://ifconfig.io/ip', timeout=10)
            return response.text.strip()
        except:
            try:
                response = requests.get('http://api.ipify.org', timeout=10)
                return response.text.strip()
            except:
                return "Unknown"
    
    @staticmethod
    def get_vpn_status():
        """Check if VPN is connected"""
        try:
            result = subprocess.run(['pgrep', 'openvpn'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def rotate_vpn():
        """Rotate to different VPN server"""
        try:
            # This would trigger the VPN rotation in the start.sh script
            # For now, we'll just simulate it
            stream_logger.log("Rotating VPN connection...", 'info')
            return True
        except Exception as e:
            stream_logger.log(f"VPN rotation failed: {str(e)}", 'error')
            return False

# User Agents (keep existing)
DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # ... keep existing user agents
]

MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # ... keep existing user agents
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
        self.vpn_manager = VPNManager()
        
    def setup_driver(self):
        try:
            chrome_options = Options()
            
            # Setup for Docker environment
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Headless mode for server
            chrome_options.add_argument("--headless=new")
            
            # Anti-detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Performance optimizations
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            
            # Set user agent
            device_type = self.config.get('device_type', 'random')
            user_agent = get_random_user_agent(device_type)
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Get current IP for logging
            current_ip = self.vpn_manager.get_current_ip()
            session_stats['current_ip'] = current_ip
            stream_logger.update_stats(session_stats)
            
            stream_logger.log(f"Browser setup - IP: {current_ip}, User Agent: {user_agent[:50]}...", 'info')
            
            # Initialize driver
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
            
        except Exception as e:
            stream_logger.log(f"Driver setup failed: {str(e)}", 'error')
            return False
    
    def check_vpn_connection(self):
        """Check and log VPN status"""
        vpn_connected = self.vpn_manager.get_vpn_status()
        current_ip = self.vpn_manager.get_current_ip()
        
        session_stats['current_ip'] = current_ip
        stream_logger.update_stats(session_stats)
        
        if vpn_connected:
            stream_logger.log(f"VPN Connected - IP: {current_ip}", 'info')
        else:
            stream_logger.log(f"No VPN - Direct Connection - IP: {current_ip}", 'warning')
        
        return vpn_connected
    
    def rotate_vpn_if_needed(self):
        """Rotate VPN based on configuration"""
        vpn_config = self.config.get('vpn_behavior', 'static')
        
        if vpn_config == 'rotate' and random.random() < 0.3:  # 30% chance to rotate
            if self.vpn_manager.rotate_vpn():
                session_stats['vpn_changes'] += 1
                stream_logger.update_stats(session_stats)
                # Wait for VPN to stabilize
                time.sleep(5)
                self.check_vpn_connection()
                return True
        return False
    
    # Keep all the existing methods (human_like_delay, human_type, human_scroll, etc.)
    # ... [All the existing browser automation methods remain the same]
    
    def human_like_delay(self, min_sec=1, max_sec=3):
        time.sleep(random.uniform(min_sec, max_sec))
    
    def human_type(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
    
    def human_scroll(self, scroll_count=3):
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
        try:
            self.driver.get("https://www.google.com")
            self.human_like_delay(2, 4)
            
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
        try:
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
        try:
            self.driver.get(url)
            self.human_like_delay(3, 6)
            self.human_scroll(random.randint(2, 4))
            return True
        except Exception as e:
            stream_logger.log(f"Visit URL failed: {str(e)}", 'error')
            return False
    
    def run_session(self, search_queries, session_num):
        global session_stats
        
        try:
            if not self.setup_driver():
                return False
            
            # Check VPN status at session start
            self.check_vpn_connection()
            
            stream_logger.log(f"Session {session_num} started", 'info')
            
            for i, item in enumerate(search_queries):
                if not is_running:
                    break
                
                # Check VPN connection periodically
                if i % 2 == 0:  # Check every 2 activities
                    self.check_vpn_connection()
                
                stream_logger.log(f"Session {session_num}, Activity {i+1}: Processing '{item}'", 'info')
                
                if item.startswith('http'):
                    success = self.visit_url(item)
                else:
                    success = self.google_search(item)
                    if success:
                        self.human_scroll(random.randint(2, 4))
                        if self.click_random_result():
                            self.human_like_delay(10, 20)
                            self.human_scroll(2)
                
                if success:
                    session_stats['pages_visited'] += 1
                    session_stats['tabs_opened'] += 1
                    stream_logger.update_stats(session_stats)
                
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

# Flask routes remain mostly the same, but update the config handling
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_automation():
    global automation_thread, is_running, session_stats
    
    if is_running:
        return jsonify({'success': False, 'error': 'Automation is already running'})
    
    config = request.json
    
    # Update session stats with initial IP
    current_ip = VPNManager.get_current_ip()
    vpn_status = VPNManager.get_vpn_status()
    
    session_stats = {
        'sessions_completed': 0,
        'tabs_opened': 0,
        'ads_clicked': 0,
        'pages_visited': 0,
        'vpn_changes': 0,
        'current_ip': current_ip,
        'vpn_status': 'Connected' if vpn_status else 'Disconnected',
        'start_time': datetime.now().isoformat()
    }
    
    stream_logger.log(f'Starting automation - IP: {current_ip}, VPN: {vpn_status}', 'info')
    is_running = True
    
    automation_thread = threading.Thread(
        target=run_automation_session,
        args=(config,)
    )
    automation_thread.daemon = True
    automation_thread.start()
    
    return jsonify({'success': True})

# Keep other routes the same...
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

@app.route('/vpn/status')
def vpn_status():
    current_ip = VPNManager.get_current_ip()
    vpn_connected = VPNManager.get_vpn_status()
    return jsonify({
        'vpn_connected': vpn_connected,
        'current_ip': current_ip
    })

@app.route('/vpn/rotate', methods=['POST'])
def rotate_vpn():
    success = VPNManager.rotate_vpn()
    return jsonify({'success': success})

def run_automation_session(config):
    global is_running, session_stats
    try:
        search_queries = [config.get('search_query', 'python programming')]
        custom_urls = config.get('custom_urls', [])
        all_items = search_queries + [url.strip() for url in custom_urls if url.strip()]
        session_count = config.get('session_count', 1)
        tab_count = min(config.get('tab_count', 3), len(all_items))
        
        stream_logger.log(f'Starting {session_count} sessions with {tab_count} tabs each', 'info')
        stream_logger.update_status('Running')
        
        for session_num in range(session_count):
            if not is_running:
                break
            stream_logger.log(f'Session {session_num + 1} started', 'info')
            session_items = random.sample(all_items, min(tab_count, len(all_items)))
            automation = BrowserAutomation(config)
            success = automation.run_session(session_items, session_num + 1)
            if success:
                session_stats['sessions_completed'] += 1
                stream_logger.update_stats(session_stats)
                stream_logger.log(f'Session {session_num + 1} completed successfully', 'success')
            else:
                stream_logger.log(f'Session {session_num + 1} failed', 'error')
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
