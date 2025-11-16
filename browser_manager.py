from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import random
import os
from config import SessionConfig

class BrowserManager:
    def __init__(self, session_config):
        self.config = session_config
        self.driver = None
        
    def setup_browser(self):
        chrome_options = Options()
        
        # Setup user agent
        chrome_options.add_argument(f"--user-agent={self.config.user_agent}")
        
        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Performance options for Render
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")  # Required for Render
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Additional options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        
        # Set Chrome binary location explicitly
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        # Initialize driver
        self.driver = webdriver.Chrome(
            options=chrome_options
        )
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def check_data_leak(self):
        """Check for IP/DNS leaks"""
        try:
            self.driver.get("https://api.ipify.org")
            time.sleep(2)
            ip_address = self.driver.find_element(By.TAG_NAME, "body").text
            print(f"Current IP: {ip_address}")
            return True
        except Exception as e:
            print(f"Data leak check failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear browser cache"""
        try:
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            self.driver.delete_all_cookies()
        except Exception as e:
            print(f"Cache clearing failed: {e}")
