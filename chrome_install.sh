#!/bin/bash
echo "🚀 Installing Chrome without apt-get..."

# Download Chrome binary langsung
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Extract deb file tanpa root
mkdir -p chrome_temp
dpkg-deb -x google-chrome-stable_current_amd64.deb chrome_temp

# Copy Chrome binary ke system path
mkdir -p /tmp/chrome
cp -r chrome_temp/opt/google/chrome/* /tmp/chrome/
cp chrome_temp/usr/bin/* /tmp/chrome/ 2>/dev/null || true

# Download ChromeDriver
wget -q https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.109/linux64/chromedriver-linux64.zip
unzip -q chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

echo "✅ Chrome installation completed!"
