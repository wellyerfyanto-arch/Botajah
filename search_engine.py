from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random

class GoogleSearch:
    def __init__(self, driver):
        self.driver = driver
    
    def perform_search(self, search_query):
        try:
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Find search box and input query
            search_box = self.driver.find_element(By.NAME, "q")
            search_box.clear()
            
            # Type like human
            for char in search_query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(1)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
            
            return True
        except Exception as e:
            print(f"Search failed: {e}")
            return False
    
    def click_random_result(self):
        """Click random search result"""
        try:
            # Find all search results
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.g h3")
            if results:
                random_result = random.choice(results[1:])  # Skip first if it's ad
                random_result.click()
                time.sleep(3)
                return True
            return False
        except Exception as e:
            print(f"Click random result failed: {e}")
            return False
    
    def click_ads_if_exist(self):
        """Click ads if available"""
        try:
            ads = self.driver.find_elements(By.CSS_SELECTOR, "[data-text-ad]")
            if ads:
                random_ad = random.choice(ads)
                random_ad.click()
                time.sleep(random.randint(10, 30))  # Stay on ad page
                self.driver.back()
                time.sleep(3)
                return True
            return False
        except Exception as e:
            print(f"Click ads failed: {e}")
            return False
