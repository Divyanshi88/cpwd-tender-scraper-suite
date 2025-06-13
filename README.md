# 🚀 CPWD Tender Scraper Suite

A Python-based scraper that automates the extraction of tender data from the [CPWD e-Tendering Portal](https://etender.cpwd.gov.in/), using multiple scraping methods to ensure high reliability and efficiency.

---

## 📖 Project Overview
The **CPWD Tender Scraper Suite** is a comprehensive tool designed to scrape the latest tenders from the CPWD e-Tendering website. It automates the tedious process of tender data collection, providing users with a CSV file containing clean and well-structured information.

This suite offers multiple scraping approaches, including browser-based and non-browser-based techniques, to maximize scraping success even if the website structure or anti-bot measures change.

---

## ✨ Key Features
- 🔎 **Automatic Navigation:** Navigates directly to the **"New Tenders" → "All"** section.
- 📥 **Tender Extraction:** Collects information for the **first 20 tenders** listed on the site.
- 💾 **CSV Export:** Saves the extracted data to a CSV file with renamed, user-friendly columns.
- 🛠️ **Multi-Approach Scraping:** Includes multiple scraping techniques:
  - Requests + BeautifulSoup
  - Selenium WebDriver
  - Undetected ChromeDriver
  - Playwright
- 🧩 **Fallback Handling:** Automatically generates sample data if scraping fails.
- 🚀 **Robust & Flexible:** Handles minor website changes and offers interactive mode for CAPTCHA resolution.

---

## 📂 Extracted Fields
The following tender details are extracted and saved:
- **Tender Reference Number** → `ref_no`
- **Tender Title / Work Description** → `title`
- **Estimated Tender Value** → `tender_value`
- **Bid Submission End Date & Time** → `bid_submission_end_date`
- **EMD Amount** → `emd`
- **Bid Opening Date & Time** → `bid_open_date`

---

## 📦 Folder Structure
cpwd-tender-scraper-suite/
├── cpwd_scraper.py
├── cpwd_scraper_bs4.py
├── cpwd_scraper_combined.py
├── cpwd_scraper_interactive.py
├── cpwd_scraper_playwright.py
├── cpwd_scraper_requests.py
├── cpwd_scraper_robust.py
├── cpwd_scraper_undetected.py
├── requirements.txt
└── README.md

yaml
Copy
Edit

---

## ⚙️ Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Divyanshi88/cpwd-tender-scraper-suite.git
   cd cpwd-tender-scraper-suite
Install the Dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Ensure Chrome Browser is Installed:

Required for Selenium-based scripts.

Make sure ChromeDriver version matches your Chrome browser version.

🚀 Usage
Run the combined script for the best performance and fallback mechanisms:

bash
Copy
Edit
python cpwd_scraper_combined.py
This script automatically tries the following scraping methods in order:

Requests + BeautifulSoup (lightweight and fast)

Selenium WebDriver (standard browser automation)

Undetected ChromeDriver (bypasses anti-bot detection)

Playwright (modern and stealthy browser automation)

👉 If all methods fail, sample fallback data will still be generated.

🛠️ Available Scripts
Script Name	Description
cpwd_scraper.py	Basic Selenium version
cpwd_scraper_bs4.py	BeautifulSoup-enhanced version
cpwd_scraper_interactive.py	Manual CAPTCHA handling version
cpwd_scraper_robust.py	Advanced error handling version
cpwd_scraper_undetected.py	Uses undetected-chromedriver
cpwd_scraper_playwright.py	Playwright-based version
cpwd_scraper_requests.py	Lightweight requests + BeautifulSoup version
cpwd_scraper_combined.py	Recommended: Tries all methods automatically

🚑 Troubleshooting
Ensure Google Chrome and ChromeDriver versions are compatible.

Try different scraping approaches if a method fails.

For CAPTCHA issues, use the interactive version.

If all scraping methods fail, the combined script will generate sample fallback data automatically.

🔧 Requirements
Python 3.8 or higher

Chrome browser (for Selenium-based methods)

Required Python libraries (listed in requirements.txt)

📜 License
This project is for educational purposes only. Use it responsibly and ensure compliance with the terms of the CPWD e-Tendering Portal.

🙌 Acknowledgements
CPWD e-Tendering Portal: https://etender.cpwd.gov.in/

Python Libraries: Selenium, BeautifulSoup, Playwright, Requests

If you find this project useful, feel free to ⭐ star the repository and share your feedback!

yaml
Copy
Edit

---

### ✅ Additional Files You May Need:
#### Example `.gitignore`
```gitignore
__pycache__/
*.pyc
*.log
*.csv
.env
Example requirements.txt
text
Copy
Edit
requests
beautifulsoup4
selenium
playwright
undetected-chromedriver
pandas
