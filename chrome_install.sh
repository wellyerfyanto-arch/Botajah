#!/bin/bash
set -ex

echo "Installing system dependencies..."
apt-get update
apt-get install -y wget unzip

echo "Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

echo "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
CHROMEDRIVER_VERSION=$(wget -q -O - "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

echo "Cleaning up..."
rm chromedriver_linux64.zip

echo "Installation completed successfully!"
google-chrome --version
chromedriver --version
