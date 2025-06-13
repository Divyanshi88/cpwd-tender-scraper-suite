# CPWD Tender Scraper

This Python script scrapes tender data from the CPWD e-Tender website (https://etender.cpwd.gov.in/).

## Features

- Navigates to the "New Tenders" tab and selects the "All" sub-tab
- Extracts details for the first 20 tenders listed
- Saves the data to a CSV file with renamed columns

## Fields Extracted

The script extracts the following fields:
1. NIT/RFP NO (saved as "ref_no")
2. Name of Work / Subwork / Packages (saved as "title")
3. Estimated Cost (saved as "tender_value")
4. Bid Submission Closing Date & Time (saved as "bid_submission_end_date")
5. EMD Amount (saved as "emd")
6. Bid Opening Date & Time (saved as "bid_open_date")

## Installation

1. Install Python 3.8 or higher
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

For the most reliable results, use the combined script:
```
python cpwd_scraper_combined.py
```

This script will try multiple approaches in sequence until one succeeds:
1. Requests + BeautifulSoup approach (no browser automation)
2. Selenium approach (standard browser automation)
3. Undetected-ChromeDriver approach (better at avoiding detection)
4. Playwright approach (modern browser automation)

If all approaches fail, it will generate sample data as a fallback.

## Alternative Scripts

Several alternative implementations are provided:

- **cpwd_scraper.py**: Basic version using Selenium
- **cpwd_scraper_bs4.py**: Enhanced version using BeautifulSoup for better parsing
- **cpwd_scraper_interactive.py**: Version that can handle CAPTCHA challenges with manual intervention
- **cpwd_scraper_robust.py**: Version with extensive error handling and multiple strategies
- **cpwd_scraper_undetected.py**: Uses undetected-chromedriver to avoid detection
- **cpwd_scraper_playwright.py**: Uses Playwright for browser automation
- **cpwd_scraper_requests.py**: Uses requests and BeautifulSoup without browser automation
- **cpwd_scraper_combined.py**: Tries all approaches in sequence

## Notes

- The scripts require various dependencies depending on the approach used
- All dependencies are listed in requirements.txt
- Some approaches require a Chrome browser to be installed
- The combined script will automatically install missing dependencies

## Troubleshooting

If you encounter issues:

1. Try running the script with different approaches
2. Check if your Chrome browser version is compatible with ChromeDriver
3. For CAPTCHA issues, use the interactive version
4. If all else fails, the combined script will generate sample data