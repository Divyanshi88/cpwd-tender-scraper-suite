import time
import csv
import pandas as pd
import os
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

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

def setup_driver(headless=True):
    """Set up and return a configured undetected ChromeDriver"""
    try:
        options = uc.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Initialize the undetected Chrome driver
        driver = uc.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize undetected Chrome driver: {e}")
        raise

def click_element_with_retry(driver, locator_strategies, max_attempts=3, wait_time=10):
    """
    Try to click an element using multiple locator strategies with retry logic
    
    Args:
        driver: Selenium WebDriver
        locator_strategies: List of tuples (By.X, "locator")
        max_attempts: Maximum number of retry attempts
        wait_time: Wait time in seconds for element to be clickable
    
    Returns:
        bool: True if click was successful, False otherwise
    """
    for attempt in range(max_attempts):
        for by_method, locator in locator_strategies:
            try:
                logger.info(f"Attempt {attempt+1}: Trying to click element with {by_method} = {locator}")
                element = WebDriverWait(driver, wait_time).until(
                    EC.element_to_be_clickable((by_method, locator))
                )
                element.click()
                logger.info(f"Successfully clicked element with {by_method} = {locator}")
                return True
            except TimeoutException:
                logger.warning(f"Timeout waiting for element with {by_method} = {locator}")
                continue
            except ElementClickInterceptedException:
                logger.warning(f"Element click intercepted for {by_method} = {locator}, trying JavaScript click")
                try:
                    driver.execute_script("arguments[0].click();", element)
                    logger.info(f"Successfully clicked element with JavaScript: {by_method} = {locator}")
                    return True
                except Exception as e:
                    logger.warning(f"JavaScript click failed: {e}")
                    continue
            except Exception as e:
                logger.warning(f"Failed to click element with {by_method} = {locator}: {e}")
                continue
        
        # If we've tried all strategies and failed, wait a bit before retrying
        if attempt < max_attempts - 1:
            logger.info(f"All click strategies failed on attempt {attempt+1}, waiting before retry...")
            time.sleep(3)
    
    logger.error("All attempts to click element failed")
    return False

def extract_tender_data(driver, soup=None):
    """
    Extract tender data from the current page
    
    Args:
        driver: Selenium WebDriver
        soup: BeautifulSoup object (optional, will be created if not provided)
    
    Returns:
        dict: Extracted tender data
    """
    if not soup:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    tender_data = {}
    
    # Define field mappings with multiple possible labels
    field_mappings = {
        "NIT/RFP NO": ["NIT/RFP NO", "NIT Number", "Tender Number", "Reference No"],
        "Name of Work / Subwork / Packages": ["Name of Work", "Work Description", "Title", "Project Name"],
        "Estimated Cost": ["Estimated Cost", "Tender Value", "Project Cost", "Estimated Value"],
        "Bid Submission Closing Date & Time": ["Bid Submission Closing Date", "Closing Date", "Submission Deadline"],
        "EMD Amount": ["EMD Amount", "Earnest Money Deposit", "EMD Value"],
        "Bid Opening Date & Time": ["Bid Opening Date", "Opening Date", "Tender Opening Date"]
    }
    
    # Function to extract field data using multiple possible labels
    def extract_field(field_labels):
        for label in field_labels:
            try:
                # Try exact match first
                field_element = soup.find('td', string=label)
                
                # If not found, try partial match
                if not field_element:
                    field_element = soup.find('td', string=lambda text: label in text if text else False)
                    
                if field_element:
                    value = field_element.find_next_sibling('td').get_text(strip=True)
                    return value
            except:
                continue
        
        # If all attempts fail, try looking for a table with these headers
        try:
            headers = soup.find_all('th')
            for header in headers:
                header_text = header.get_text(strip=True)
                for label in field_labels:
                    if label in header_text:
                        # Find the corresponding cell in the same column
                        index = list(header.parent.find_all('th')).index(header)
                        row = header.parent.find_next_sibling('tr')
                        if row:
                            cells = row.find_all('td')
                            if index < len(cells):
                                return cells[index].get_text(strip=True)
        except:
            pass
            
        return "N/A"
    
    # Extract all required fields
    for field_key, possible_labels in field_mappings.items():
        tender_data[field_key] = extract_field(possible_labels)
    
    return tender_data

def scrape_cpwd_tenders(headless=True):
    """
    Scrape tender data from CPWD website with robust error handling
    
    Args:
        headless (bool): Whether to run in headless mode
    
    Returns:
        list: List of dictionaries containing tender data
    """
    driver = None
    try:
        driver = setup_driver(headless=headless)
        
        # Navigate to the CPWD website
        logger.info("Navigating to CPWD website...")
        driver.get("https://etender.cpwd.gov.in/")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Check if CAPTCHA is present and handle it if in interactive mode
        if not headless:
            input("If there's a CAPTCHA, please solve it manually and press Enter to continue...")
        
        # Click on the "New Tenders" tab with multiple strategies
        logger.info("Clicking on 'New Tenders' tab...")
        new_tenders_strategies = [
            (By.XPATH, "//a[contains(text(), 'New Tenders')]"),
            (By.LINK_TEXT, "New Tenders"),
            (By.PARTIAL_LINK_TEXT, "New Tender"),
            (By.CSS_SELECTOR, "a[href*='new-tenders']")
        ]
        
        if not click_element_with_retry(driver, new_tenders_strategies):
            # Try direct navigation as a last resort
            logger.info("Trying direct navigation to New Tenders page...")
            driver.get("https://etender.cpwd.gov.in/new-tenders")
            time.sleep(5)
        
        # Click on the "All" sub-tab with multiple strategies
        logger.info("Clicking on 'All' sub-tab...")
        all_tab_strategies = [
            (By.XPATH, "//a[contains(text(), 'All')]"),
            (By.LINK_TEXT, "All"),
            (By.CSS_SELECTOR, "a[href*='all']"),
            (By.CSS_SELECTOR, "ul.nav-tabs li a")  # Try first tab if specific locators fail
        ]
        
        if not click_element_with_retry(driver, all_tab_strategies):
            # If we can't click the All tab, try to continue anyway
            logger.warning("Could not click 'All' tab, attempting to continue...")
        
        # Wait for the tender list to load
        time.sleep(5)
        
        # Take a screenshot for debugging
        driver.save_screenshot("tender_list.png")
        logger.info(f"Screenshot saved to {os.path.abspath('tender_list.png')}")
        
        # Extract data for the first 20 tenders
        logger.info("Extracting tender data...")
        tenders_data = []
        
        # Try multiple strategies to find tender rows
        tender_rows = []
        row_locator_strategies = [
            (By.XPATH, "//table[@id='tendersTable']/tbody/tr"),
            (By.CSS_SELECTOR, "table.table tbody tr"),
            (By.CSS_SELECTOR, "table tbody tr"),
            (By.XPATH, "//tr[contains(@class, 'tender')]"),
            (By.XPATH, "//div[contains(@class, 'tender-list')]//tr")
        ]
        
        for by_method, locator in row_locator_strategies:
            try:
                logger.info(f"Trying to find tender rows with {by_method} = {locator}")
                rows = driver.find_elements(by_method, locator)
                if rows:
                    tender_rows = rows
                    logger.info(f"Found {len(rows)} tender rows with {by_method} = {locator}")
                    break
            except Exception as e:
                logger.warning(f"Failed to find tender rows with {by_method} = {locator}: {e}")
        
        if not tender_rows:
            logger.error("Could not find any tender rows with any strategy")
            # Try to parse the page with BeautifulSoup as a last resort
            logger.info("Attempting to parse page with BeautifulSoup...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables on the page")
            
            if tables:
                # Try to find a table with tender data
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 1:  # At least one header row and one data row
                        logger.info(f"Found table with {len(rows)} rows, attempting to extract data")
                        # Extract data from this table
                        headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
                        logger.info(f"Table headers: {headers}")
                        
                        for i, row in enumerate(rows[1:21]):  # Get up to 20 data rows
                            try:
                                cells = row.find_all('td')
                                tender_data = {}
                                
                                # Map headers to our required fields
                                for j, header in enumerate(headers):
                                    if j < len(cells):
                                        if "NIT" in header or "RFP" in header:
                                            tender_data["NIT/RFP NO"] = cells[j].get_text(strip=True)
                                        elif "Work" in header or "Title" in header:
                                            tender_data["Name of Work / Subwork / Packages"] = cells[j].get_text(strip=True)
                                        elif "Cost" in header or "Value" in header:
                                            tender_data["Estimated Cost"] = cells[j].get_text(strip=True)
                                        elif "Closing" in header or "Submission" in header:
                                            tender_data["Bid Submission Closing Date & Time"] = cells[j].get_text(strip=True)
                                        elif "EMD" in header:
                                            tender_data["EMD Amount"] = cells[j].get_text(strip=True)
                                        elif "Opening" in header:
                                            tender_data["Bid Opening Date & Time"] = cells[j].get_text(strip=True)
                                
                                # Ensure all required fields exist
                                for field in ["NIT/RFP NO", "Name of Work / Subwork / Packages", "Estimated Cost", 
                                             "Bid Submission Closing Date & Time", "EMD Amount", "Bid Opening Date & Time"]:
                                    if field not in tender_data:
                                        tender_data[field] = "N/A"
                                
                                tenders_data.append(tender_data)
                                logger.info(f"Extracted data for tender {i+1}")
                            except Exception as e:
                                logger.error(f"Error extracting data from row {i+1}: {e}")
                        
                        if tenders_data:
                            logger.info(f"Successfully extracted data for {len(tenders_data)} tenders from table")
                            return tenders_data
        
        # Limit to first 20 rows
        tender_rows = tender_rows[:20] if len(tender_rows) > 20 else tender_rows
        
        for i, row in enumerate(tender_rows):
            logger.info(f"Processing tender {i+1}/{len(tender_rows)}...")
            
            try:
                # Click on the row to view details
                try:
                    row.click()
                except ElementClickInterceptedException:
                    logger.warning("Click intercepted, trying JavaScript click")
                    driver.execute_script("arguments[0].click();", row)
                except Exception as e:
                    logger.error(f"Error clicking row: {e}")
                    # Try to find a link or button in the row
                    try:
                        links = row.find_elements(By.TAG_NAME, "a")
                        if links:
                            links[0].click()
                        else:
                            buttons = row.find_elements(By.TAG_NAME, "button")
                            if buttons:
                                buttons[0].click()
                            else:
                                # Try clicking the first cell
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if cells:
                                    cells[0].click()
                                else:
                                    raise Exception("No clickable element found in row")
                    except Exception as nested_e:
                        logger.error(f"All click attempts failed: {nested_e}")
                        continue
                
                time.sleep(2)
                
                # Take a screenshot of the details page
                driver.save_screenshot(f"tender_details_{i+1}.png")
                
                # Extract tender data
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                tender_data = extract_tender_data(driver, soup)
                
                tenders_data.append(tender_data)
                logger.info(f"Successfully extracted data for tender {i+1}")
                
                # Go back to the tender list
                try:
                    back_strategies = [
                        (By.XPATH, "//button[contains(text(), 'Back')]"),
                        (By.XPATH, "//a[contains(text(), 'Back')]"),
                        (By.CSS_SELECTOR, "button.back-button"),
                        (By.CSS_SELECTOR, "a.back-link")
                    ]
                    
                    if not click_element_with_retry(driver, back_strategies, max_attempts=2):
                        logger.warning("Back button not found, using browser back")
                        driver.back()
                except Exception as e:
                    logger.error(f"Error navigating back: {e}")
                    driver.back()
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing tender {i+1}: {e}")
                # Try to recover and continue with next tender
                try:
                    driver.back()
                    time.sleep(2)
                except:
                    logger.error("Failed to recover, continuing...")
        
        return tenders_data
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if driver:
            logger.info("Taking screenshot for debugging...")
            driver.save_screenshot("error_screenshot.png")
            logger.info(f"Screenshot saved to {os.path.abspath('error_screenshot.png')}")
        return []
        
    finally:
        # Close the browser
        if driver:
            driver.quit()

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

def main():
    logger.info("Starting CPWD tender scraping...")
    
    # First try in headless mode
    logger.info("Attempting to scrape in headless mode...")
    tenders_data = scrape_cpwd_tenders(headless=True)
    
    # If headless mode fails or returns insufficient data, try interactive mode
    if not tenders_data or len(tenders_data) < 5:  # Arbitrary threshold
        logger.info("Headless mode failed or returned insufficient data. Switching to interactive mode...")
        tenders_data = scrape_cpwd_tenders(headless=False)
    
    if tenders_data:
        logger.info(f"Successfully scraped {len(tenders_data)} tenders.")
        save_to_csv(tenders_data)
    else:
        logger.error("Failed to scrape tender data.")

if __name__ == "__main__":
    main()