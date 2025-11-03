#!/bin/bash
echo "🚀 Installing Chrome without apt-get..."

# Download Chrome
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Extract without root
mkdir -p chrome_temp
dpkg-deb -x google-chrome-stable_current_amd64.deb chrome_temp

# Copy Chrome files
mkdir -p /tmp/chrome
cp -r chrome_temp/opt/google/chrome/* /tmp/chrome/

# Download ChromeDriver
wget -q https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.109/linux64/chromedriver-linux64.zip
unzip -q chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Download VPN extension
wget -q -O touchvpn.crx "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=109.0&x=id%3Dbihmplhobchoageeokmgbdihknkjbknd%26installsource%3Dwebstore%26uc"

echo "✅ Chrome installation completed!"
