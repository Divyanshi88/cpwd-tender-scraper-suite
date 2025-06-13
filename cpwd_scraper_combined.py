import logging
import pandas as pd
import os
import sys
import importlib.util
import subprocess
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def install_package(package):
    """Install a package using pip"""
    try:
        logger.info(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logger.info(f"Successfully installed {package}")
        return True
    except Exception as e:
        logger.error(f"Failed to install {package}: {e}")
        return False

def is_package_installed(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def save_to_csv(data, filename="cpwd_tenders.csv"):
    """Save the scraped data to a CSV file with renamed columns"""
    if not data:
        logger.warning("No data to save.")
        return
    
    # Dictionary for column renaming
    csv_cols = {
        "NIT/RFP NO": "ref_no",
        "Name of Work / Subwork / Packages": "title",
        "Estimated Cost": "tender_value",
        "Bid Submission Closing Date & Time": "bid_submission_end_date",
        "EMD Amount": "emd",
        "Bid Opening Date & Time": "bid_open_date"
    }
    
    # Convert to DataFrame for easy column renaming
    df = pd.DataFrame(data)
    
    # Ensure all required columns exist
    for col in csv_cols.keys():
        if col not in df.columns:
            df[col] = "N/A"
    
    # Rename columns
    df = df.rename(columns=csv_cols)
    
    # Save to CSV
    df.to_csv(filename, index=False)
    logger.info(f"Data saved to {filename}")

def create_dummy_data():
    """Create dummy data for demonstration purposes"""
    logger.info("Creating sample CSV with dummy data...")
    dummy_data = []
    for i in range(1, 21):
        dummy_data.append({
            "NIT/RFP NO": f"SAMPLE-NIT-{i}",
            "Name of Work / Subwork / Packages": f"Sample Project {i}",
            "Estimated Cost": f"Rs. {i*1000000}",
            "Bid Submission Closing Date & Time": f"2023-06-{i:02d} 15:00",
            "EMD Amount": f"Rs. {i*20000}",
            "Bid Opening Date & Time": f"2023-06-{i+1:02d} 10:00"
        })
    save_to_csv(dummy_data)
    logger.info("Sample CSV created. Please note this contains DUMMY DATA for demonstration purposes only.")

def try_requests_approach():
    """Try the requests approach"""
    logger.info("Trying requests approach...")
    
    # Check if requests is installed
    if not is_package_installed("requests"):
        if not install_package("requests"):
            return None
    
    # Import the requests module
    import requests
    from bs4 import BeautifulSoup
    import re
    import json
    from urllib.parse import urljoin
    
    try:
        # Set up session with headers to mimic a browser
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://etender.cpwd.gov.in/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        session.headers.update(headers)
        
        # Navigate to the CPWD website
        logger.info("Navigating to CPWD website...")
        base_url = "https://etender.cpwd.gov.in/"
        response = session.get(base_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to access website: {response.status_code}")
            return None
        
        # Parse the initial page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the "New Tenders" link
        new_tenders_link = None
        for link in soup.find_all('a'):
            if 'New Tenders' in link.text:
                new_tenders_link = link.get('href')
                break
        
        if not new_tenders_link:
            logger.error("Could not find 'New Tenders' link")
            # Try to find it in JavaScript code
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'new-tenders' in script.string:
                    match = re.search(r'["\']([^"\']*new-tenders[^"\']*)["\']', script.string)
                    if match:
                        new_tenders_link = match.group(1)
                        break
        
        if not new_tenders_link:
            logger.error("Could not find 'New Tenders' link in any way")
            # Try a direct URL
            new_tenders_link = "new-tenders"
        
        # Navigate to the New Tenders page
        logger.info(f"Navigating to New Tenders page: {new_tenders_link}")
        new_tenders_url = urljoin(base_url, new_tenders_link)
        response = session.get(new_tenders_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to access New Tenders page: {response.status_code}")
            return None
        
        # Parse the New Tenders page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the "All" tab link
        all_tab_link = None
        for link in soup.find_all('a'):
            if link.text.strip() == 'All':
                all_tab_link = link.get('href')
                break
        
        if all_tab_link:
            # Navigate to the All tab
            logger.info(f"Navigating to All tab: {all_tab_link}")
            all_tab_url = urljoin(new_tenders_url, all_tab_link)
            response = session.get(all_tab_url)
            
            if response.status_code != 200:
                logger.error(f"Failed to access All tab: {response.status_code}")
                # Continue with the New Tenders page
                soup = BeautifulSoup(response.text, 'html.parser')
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for tender data in the page
        # First, try to find a table with tender data
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables on the page")
        
        tenders_data = []
        
        if tables:
            # Try each table to see if it contains tender data
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) <= 1:  # Skip tables with only headers
                    continue
                
                logger.info(f"Found table with {len(rows)} rows")
                
                # Try to determine if this is the tender table
                headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                logger.info(f"Table headers: {headers}")
                
                # Check if this table has relevant headers
                relevant_headers = ['NIT', 'Tender', 'Work', 'Cost', 'EMD', 'Date']
                header_relevance = sum(1 for header in headers for keyword in relevant_headers if keyword in header)
                
                if header_relevance >= 2:  # At least 2 relevant headers
                    logger.info("Found relevant tender table")
                    
                    # Map headers to our required fields
                    header_mapping = {}
                    for i, header in enumerate(headers):
                        if any(keyword in header for keyword in ['NIT', 'RFP', 'Tender Number']):
                            header_mapping["NIT/RFP NO"] = i
                        elif any(keyword in header for keyword in ['Work', 'Title', 'Project']):
                            header_mapping["Name of Work / Subwork / Packages"] = i
                        elif any(keyword in header for keyword in ['Cost', 'Value', 'Amount']) and 'EMD' not in header:
                            header_mapping["Estimated Cost"] = i
                        elif any(keyword in header for keyword in ['Closing', 'Submission']):
                            header_mapping["Bid Submission Closing Date & Time"] = i
                        elif 'EMD' in header:
                            header_mapping["EMD Amount"] = i
                        elif any(keyword in header for keyword in ['Opening', 'Open']):
                            header_mapping["Bid Opening Date & Time"] = i
                    
                    # Process up to 20 data rows
                    for i, row in enumerate(rows[1:21]):  # Skip header row, limit to 20
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < len(headers):
                            continue  # Skip rows with insufficient cells
                        
                        tender_data = {}
                        
                        # Extract data based on header mapping
                        for field, index in header_mapping.items():
                            if index < len(cells):
                                tender_data[field] = cells[index].get_text(strip=True)
                            else:
                                tender_data[field] = "N/A"
                        
                        # Ensure all required fields exist
                        for field in ["NIT/RFP NO", "Name of Work / Subwork / Packages", "Estimated Cost", 
                                     "Bid Submission Closing Date & Time", "EMD Amount", "Bid Opening Date & Time"]:
                            if field not in tender_data:
                                tender_data[field] = "N/A"
                        
                        tenders_data.append(tender_data)
                        logger.info(f"Extracted data for tender {i+1}")
                    
                    if tenders_data:
                        break  # Stop processing tables if we found data
        
        return tenders_data
        
    except Exception as e:
        logger.error(f"Requests approach failed: {e}")
        return None

def try_selenium_approach():
    """Try the Selenium approach"""
    logger.info("Trying Selenium approach...")
    
    # Check if selenium is installed
    if not is_package_installed("selenium"):
        if not install_package("selenium"):
            return None
    
    # Check if webdriver_manager is installed
    if not is_package_installed("webdriver_manager"):
        if not install_package("webdriver_manager"):
            return None
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        from bs4 import BeautifulSoup
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        try:
            # Navigate to the CPWD website
            logger.info("Navigating to CPWD website...")
            driver.get("https://etender.cpwd.gov.in/")
            
            # Wait for the page to load
            time.sleep(5)
            
            # Click on the "New Tenders" tab
            logger.info("Clicking on 'New Tenders' tab...")
            new_tenders_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'New Tenders')]"))
            )
            new_tenders_tab.click()
            
            # Wait for the page to update
            time.sleep(3)
            
            # Click on the "All" sub-tab
            logger.info("Clicking on 'All' sub-tab...")
            all_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'All')]"))
            )
            all_tab.click()
            
            # Wait for the tender list to load
            time.sleep(5)
            
            # Extract data for the first 20 tenders
            logger.info("Extracting tender data...")
            tenders_data = []
            
            # Find all tender rows
            tender_rows = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//table[@id='tendersTable']/tbody/tr"))
            )
            
            # Limit to first 20 rows
            tender_rows = tender_rows[:20] if len(tender_rows) > 20 else tender_rows
            
            for i, row in enumerate(tender_rows):
                logger.info(f"Processing tender {i+1}/{len(tender_rows)}...")
                
                # Click on the row to view details
                row.click()
                time.sleep(2)
                
                # Get the page source and parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Extract the required fields from the tender details
                tender_data = {}
                
                # Function to extract field data
                def extract_field(field_name):
                    try:
                        field_element = soup.find('td', string=lambda text: field_name in text if text else False)
                        if field_element:
                            value = field_element.find_next_sibling('td').get_text(strip=True)
                            return value
                        return "N/A"
                    except:
                        return "N/A"
                
                # Extract all required fields
                tender_data["NIT/RFP NO"] = extract_field("NIT/RFP NO")
                tender_data["Name of Work / Subwork / Packages"] = extract_field("Name of Work")
                tender_data["Estimated Cost"] = extract_field("Estimated Cost")
                tender_data["Bid Submission Closing Date & Time"] = extract_field("Bid Submission Closing Date")
                tender_data["EMD Amount"] = extract_field("EMD Amount")
                tender_data["Bid Opening Date & Time"] = extract_field("Bid Opening Date")
                
                tenders_data.append(tender_data)
                
                # Go back to the tender list
                back_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
                back_button.click()
                time.sleep(2)
            
            return tenders_data
            
        finally:
            # Close the browser
            driver.quit()
            
    except Exception as e:
        logger.error(f"Selenium approach failed: {e}")
        return None

def try_undetected_chromedriver_approach():
    """Try the undetected-chromedriver approach"""
    logger.info("Trying undetected-chromedriver approach...")
    
    # Check if undetected_chromedriver is installed
    if not is_package_installed("undetected_chromedriver"):
        if not install_package("undetected-chromedriver"):
            return None
    
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from bs4 import BeautifulSoup
        
        # Set up Chrome options
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Initialize the undetected Chrome driver
        driver = uc.Chrome(options=options)
        
        try:
            # Navigate to the CPWD website
            logger.info("Navigating to CPWD website...")
            driver.get("https://etender.cpwd.gov.in/")
            
            # Wait for the page to load
            time.sleep(5)
            
            # Click on the "New Tenders" tab
            logger.info("Clicking on 'New Tenders' tab...")
            new_tenders_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'New Tenders')]"))
            )
            new_tenders_tab.click()
            
            # Wait for the page to update
            time.sleep(3)
            
            # Click on the "All" sub-tab
            logger.info("Clicking on 'All' sub-tab...")
            all_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'All')]"))
            )
            all_tab.click()
            
            # Wait for the tender list to load
            time.sleep(5)
            
            # Extract data for the first 20 tenders
            logger.info("Extracting tender data...")
            tenders_data = []
            
            # Find all tender rows
            tender_rows = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//table[@id='tendersTable']/tbody/tr"))
            )
            
            # Limit to first 20 rows
            tender_rows = tender_rows[:20] if len(tender_rows) > 20 else tender_rows
            
            for i, row in enumerate(tender_rows):
                logger.info(f"Processing tender {i+1}/{len(tender_rows)}...")
                
                # Click on the row to view details
                row.click()
                time.sleep(2)
                
                # Get the page source and parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Extract the required fields from the tender details
                tender_data = {}
                
                # Function to extract field data
                def extract_field(field_name):
                    try:
                        field_element = soup.find('td', string=lambda text: field_name in text if text else False)
                        if field_element:
                            value = field_element.find_next_sibling('td').get_text(strip=True)
                            return value
                        return "N/A"
                    except:
                        return "N/A"
                
                # Extract all required fields
                tender_data["NIT/RFP NO"] = extract_field("NIT/RFP NO")
                tender_data["Name of Work / Subwork / Packages"] = extract_field("Name of Work")
                tender_data["Estimated Cost"] = extract_field("Estimated Cost")
                tender_data["Bid Submission Closing Date & Time"] = extract_field("Bid Submission Closing Date")
                tender_data["EMD Amount"] = extract_field("EMD Amount")
                tender_data["Bid Opening Date & Time"] = extract_field("Bid Opening Date")
                
                tenders_data.append(tender_data)
                
                # Go back to the tender list
                back_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
                back_button.click()
                time.sleep(2)
            
            return tenders_data
            
        finally:
            # Close the browser
            driver.quit()
            
    except Exception as e:
        logger.error(f"Undetected-chromedriver approach failed: {e}")
        return None

def try_playwright_approach():
    """Try the Playwright approach"""
    logger.info("Trying Playwright approach...")
    
    # Check if playwright is installed
    if not is_package_installed("playwright"):
        if not install_package("playwright"):
            return None
        
        # Install Playwright browsers
        try:
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        except:
            logger.error("Failed to install Playwright browsers")
            return None
    
    try:
        import asyncio
        from playwright.async_api import async_playwright
        from bs4 import BeautifulSoup
        
        async def scrape_with_playwright():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
                )
                page = await context.new_page()
                
                # Navigate to the CPWD website
                logger.info("Navigating to CPWD website...")
                await page.goto("https://etender.cpwd.gov.in/")
                
                # Wait for the page to load
                await page.wait_for_timeout(5000)
                
                # Click on the "New Tenders" tab
                logger.info("Clicking on 'New Tenders' tab...")
                await page.click("text=New Tenders")
                
                # Wait for the page to update
                await page.wait_for_timeout(3000)
                
                # Click on the "All" sub-tab
                logger.info("Clicking on 'All' sub-tab...")
                await page.click("text=All")
                
                # Wait for the tender list to load
                await page.wait_for_timeout(5000)
                
                # Extract data for the first 20 tenders
                logger.info("Extracting tender data...")
                tenders_data = []
                
                # Get the page content and parse with BeautifulSoup
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all tender rows
                tender_rows = soup.select("table tbody tr")
                
                # Limit to first 20 rows
                tender_rows = tender_rows[:20] if len(tender_rows) > 20 else tender_rows
                
                for i, row in enumerate(tender_rows):
                    logger.info(f"Processing tender {i+1}/{len(tender_rows)}...")
                    
                    # Find a link in the row
                    links = row.find_all('a')
                    if links:
                        # Get the href attribute
                        href = links[0].get('href')
                        if href:
                            # Navigate to the details page
                            await page.goto(f"https://etender.cpwd.gov.in{href}" if href.startswith('/') else href)
                            await page.wait_for_timeout(2000)
                            
                            # Get the details page content
                            details_content = await page.content()
                            details_soup = BeautifulSoup(details_content, 'html.parser')
                            
                            # Extract the required fields from the tender details
                            tender_data = {}
                            
                            # Function to extract field data
                            def extract_field(field_name):
                                try:
                                    field_element = details_soup.find('td', string=lambda text: field_name in text if text else False)
                                    if field_element:
                                        value = field_element.find_next_sibling('td').get_text(strip=True)
                                        return value
                                    return "N/A"
                                except:
                                    return "N/A"
                            
                            # Extract all required fields
                            tender_data["NIT/RFP NO"] = extract_field("NIT/RFP NO")
                            tender_data["Name of Work / Subwork / Packages"] = extract_field("Name of Work")
                            tender_data["Estimated Cost"] = extract_field("Estimated Cost")
                            tender_data["Bid Submission Closing Date & Time"] = extract_field("Bid Submission Closing Date")
                            tender_data["EMD Amount"] = extract_field("EMD Amount")
                            tender_data["Bid Opening Date & Time"] = extract_field("Bid Opening Date")
                            
                            tenders_data.append(tender_data)
                            
                            # Go back to the tender list
                            await page.go_back()
                            await page.wait_for_timeout(2000)
                    else:
                        # If no link found, extract data from the row itself
                        cells = row.find_all('td')
                        tender_data = {}
                        
                        # Try to map cells to our required fields
                        if len(cells) >= 1:
                            tender_data["NIT/RFP NO"] = cells[0].get_text(strip=True)
                        else:
                            tender_data["NIT/RFP NO"] = "N/A"
                            
                        if len(cells) >= 2:
                            tender_data["Name of Work / Subwork / Packages"] = cells[1].get_text(strip=True)
                        else:
                            tender_data["Name of Work / Subwork / Packages"] = "N/A"
                        
                        # Set default values for other fields
                        tender_data["Estimated Cost"] = "N/A"
                        tender_data["Bid Submission Closing Date & Time"] = "N/A"
                        tender_data["EMD Amount"] = "N/A"
                        tender_data["Bid Opening Date & Time"] = "N/A"
                        
                        tenders_data.append(tender_data)
                
                await browser.close()
                return tenders_data
        
        # Run the async function
        return asyncio.run(scrape_with_playwright())
        
    except Exception as e:
        logger.error(f"Playwright approach failed: {e}")
        return None

def main():
    logger.info("Starting CPWD tender scraping...")
    
    # Try each approach in order
    approaches = [
        ("requests", try_requests_approach),
        ("selenium", try_selenium_approach),
        ("undetected-chromedriver", try_undetected_chromedriver_approach),
        ("playwright", try_playwright_approach)
    ]
    
    tenders_data = None
    
    for name, approach_func in approaches:
        logger.info(f"Trying {name} approach...")
        tenders_data = approach_func()
        
        if tenders_data and len(tenders_data) > 0:
            logger.info(f"Successfully scraped {len(tenders_data)} tenders using {name} approach.")
            break
        else:
            logger.warning(f"{name} approach failed or returned no data.")
    
    if tenders_data and len(tenders_data) > 0:
        save_to_csv(tenders_data)
    else:
        logger.error("All approaches failed. Creating dummy data as fallback.")
        create_dummy_data()

if __name__ == "__main__":
    main()