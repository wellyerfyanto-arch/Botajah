import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

class HumanBehavior:
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
    
    def human_scroll(self, scroll_count=3):
        """Scroll like human with variations"""
        for i in range(scroll_count):
            # Random scroll patterns
            scroll_type = random.choice(["smooth", "quick", "slow"])
            
            if scroll_type == "smooth":
                scroll_pixels = random.randint(300, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            elif scroll_type == "quick":
                scroll_pixels = random.randint(500, 1200)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_pixels});")
            else:  # slow
                current_pos = self.driver.execute_script("return window.pageYOffset;")
                target_pos = current_pos + random.randint(400, 1000)
                for pos in range(current_pos, target_pos, 10):
                    self.driver.execute_script(f"window.scrollTo(0, {pos});")
                    time.sleep(0.05)
            
            time.sleep(random.uniform(2, 5))
            
            # Random mouse movements
            self.random_mouse_movement()
    
    def random_mouse_movement(self):
        """Simulate random mouse movements"""
        try:
            width = self.driver.execute_script("return window.innerWidth;")
            height = self.driver.execute_script("return window.innerHeight;")
            
            for _ in range(3):
                x = random.randint(0, width)
                y = random.randint(0, height)
                self.actions.move_by_offset(x, y).perform()
                time.sleep(0.2)
        except:
            pass
    
    def reading_behavior(self, duration=30):
        """Simulate reading behavior"""
        start_time = time.time()
        while time.time() - start_time < duration:
            # Random activities during reading
            activity = random.choice(["scroll", "pause", "click_links"])
            
            if activity == "scroll":
                self.human_scroll(1)
            elif activity == "pause":
                time.sleep(random.uniform(5, 15))
            elif activity == "click_links":
                self.click_random_links()
    
    def click_random_links(self):
        """Click random links on page"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            if links:
                valid_links = [link for link in links if link.is_displayed() and link.is_enabled()]
                if valid_links:
                    random_link = random.choice(valid_links[:10])  # First 10 links
                    random_link.click()
                    time.sleep(random.randint(5, 15))
                    self.driver.back()
                    time.sleep(3)
        except Exception as e:
            print(f"Click random links failed: {e}")
