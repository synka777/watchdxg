# Watchdxg

## 🔍 Overview
Watchdxg is a Python-based scraper that monitors and extracts posts from X (formerly Twitter) using Selenium and BeautifulSoup.
The script logs in to an X account, performs advanced searches, and retrieves details such as post content, user handles, timestamps, and interaction statistics.
The end goal here is to get alerts when a post matching a particular X search is found.

## ⚠️ ***DISCLAIMER: X's TOU/TOS prohibit automated tools on their platform. USE AT YOUR OWN RISK*** ⚠️

## 👀 Features
- Automates login to X using Selenium
- Uses BeautifulSoup to parse and extract post details
- Retrieves information such as:
  - Display name
  - User handle
  - Timestamp
  - Post text
  - Replies, reposts, likes, and views
  - Reply and repost status
- Supports advanced search queries
- Avoids duplicate processing using history logging

## 📄 Requirements
### Dependencies
Ensure you have the following Python libraries installed:
```bash
pip install selenium beautifulsoup4 environs
```

### WebDriver
This script requires GeckoDriver for Selenium (for Firefox). Download it from:
- [GeckoDriver](https://github.com/mozilla/geckodriver/releases)

Place `geckodriver` in the script's directory.

## ⚡ Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/synka777/watchdxg.git
   cd watchdxg
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project directory and add your credentials:
   ```env
   USERNAME=your_x_username
   PASSWORD=your_x_password
   CONTACT=your_contact_info_if_needed
   ```

## 🟢 Usage
### Running the Script
To start scraping X posts, run:
```bash
python main.py
```

### ⬆️ Output
- Extracted posts will be printed in the console.
