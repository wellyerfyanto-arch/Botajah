import random
from datetime import datetime

# User Agents
DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"
]

# VPN Extensions (free)
VPN_EXTENSIONS = [
    "https://chrome.google.com/webstore/detail/touch-vpn/bihmplhobchoageeokmgbdihknkjbknd",
    "https://chrome.google.com/webstore/detail/hotspot-shield-free-vpn-p/nlbejmccbhkncgokjcmghpfloaajcffj",
    "https://chrome.google.com/webstore/detail/betternet-unlimited-free/gjknjjomckknofjidppipffbpoekiipm"
]

# Session configuration
class SessionConfig:
    def __init__(self):
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.user_agent = self.get_random_user_agent()
        self.vpn_extension = random.choice(VPN_EXTENSIONS)
        self.tab_count = random.randint(2, 5)
        self.session_duration = random.randint(300, 900)  # 5-15 minutes
    
    def get_random_user_agent(self):
        if random.choice([True, False]):
            return random.choice(DESKTOP_USER_AGENTS)
        else:
            return random.choice(MOBILE_USER_AGENTS)
