#!/usr/bin/env python3
"""
Script untuk download VPN extensions
Jalankan script ini secara manual jika perlu update extensions
"""

import os
import requests

def download_vpn_extensions():
    """Download semua VPN extensions yang diperlukan"""
    
    vpn_extensions = {
        "touchvpn": {
            "url": "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=109.0&x=id%3Dbihmplhobchoageeokmgbdihknkjbknd%26installsource%3Dwebstore%26uc",
            "filename": "touch_vpn.crx"
        },
        "hotspotshield": {
            "url": "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=109.0&x=id%3Dnlbejmccbhkncgokjcmghpfloaajcffj%26installsource%3Dwebstore%26uc", 
            "filename": "hotspot_shield.crx"
        }
    }
    
    # Buat folder extensions jika belum ada
    os.makedirs("extensions", exist_ok=True)
    
    for name, info in vpn_extensions.items():
        output_path = f"extensions/{info['filename']}"
        
        if not os.path.exists(output_path):
            print(f"Downloading {name}...")
            try:
                response = requests.get(info['url'], stream=True)
                with open(output_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                print(f"✅ {name} downloaded successfully")
            except Exception as e:
                print(f"❌ Error downloading {name}: {e}")
        else:
            print(f"✅ {name} already exists")

if __name__ == "__main__":
    download_vpn_extensions()
