import time
import random
from browser_manager import BrowserManager
from search_engine import GoogleSearch
from human_behavior import HumanBehavior
from config import SessionConfig

class SessionManager:
    def __init__(self):
        self.sessions = []
    
    def create_session(self, search_queries, session_config=None):
        if session_config is None:
            session_config = {}
        
        config = SessionConfig()
        
        # Override with session config
        if 'device_type' in session_config:
            if session_config['device_type'] == 'mobile':
                config.user_agent = random.choice(config.MOBILE_USER_AGENTS)
            elif session_config['device_type'] == 'desktop':
                config.user_agent = random.choice(config.DESKTOP_USER_AGENTS)
        
        if 'tab_count' in session_config:
            config.tab_count = session_config['tab_count']
        
        if 'vpn_extension' in session_config and session_config['vpn_extension'] != 'random':
            # Map to specific VPN extension
            vpn_map = {
                'touchvpn': "https://chrome.google.com/webstore/detail/touch-vpn/bihmplhobchoageeokmgbdihknkjbknd",
                'hotspotshield': "https://chrome.google.com/webstore/detail/hotspot-shield-free-vpn-p/nlbejmccbhkncgokjcmghpfloaajcffj",
                'betternet': "https://chrome.google.com/webstore/detail/betternet-unlimited-free/gjknjjomckknofjidppipffbpoekiipm"
            }
            config.vpn_extension = vpn_map.get(session_config['vpn_extension'], config.vpn_extension)
        
        browser_manager = BrowserManager(config)
        
        try:
            # Setup browser
            driver = browser_manager.setup_browser()
            google_search = GoogleSearch(driver)
            human_behavior = HumanBehavior(driver)
            
            print(f"Starting session: {config.session_id}")
            
            # Check data leak
            browser_manager.check_data_leak()
            
            # Perform searches and activities
            for query in search_queries:
                if query.startswith('http'):
                    # Direct URL visit
                    driver.get(query)
                    time.sleep(3)
                    human_behavior.human_scroll(random.randint(2, 4))
                    human_behavior.reading_behavior(random.randint(20, 40))
                else:
                    # Google search
                    if google_search.perform_search(query):
                        human_behavior.human_scroll(random.randint(2, 4))
                        google_search.click_ads_if_exist()
                        
                        if google_search.click_random_result():
                            human_behavior.reading_behavior(random.randint(20, 60))
                            human_behavior.click_random_links()
                            human_behavior.human_scroll(2)
            
            return True
            
        except Exception as e:
            print(f"Session error: {e}")
            return False
        
        finally:
            # Cleanup
            if browser_manager.driver:
                browser_manager.clear_cache()
                browser_manager.driver.quit()
    
    def run_multiple_sessions(self, search_queries_list, session_count=3):
        for i in range(session_count):
            print(f"Running session {i+1}/{session_count}")
            self.create_session(search_queries_list[i % len(search_queries_list)])
            
            if i < session_count - 1:
                wait_time = random.randint(30, 120)
                print(f"Waiting {wait_time} seconds before next session...")
                time.sleep(wait_time)
