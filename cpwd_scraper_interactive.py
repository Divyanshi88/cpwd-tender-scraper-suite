import time
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os

def setup_driver(headless=False):
    """Set up and return a configured Chrome webdriver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add user agent to appear more like a regular browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_cpwd_tenders(headless=False):
    """
    Scrape tender data from CPWD website
    
    Args:
        headless (bool): Whether to run in headless mode. Set to False if manual CAPTCHA solving is needed.
    """
    driver = setup_driver(headless=headless)
    
    try:
        # Navigate to the CPWD website
        print("Navigating to CPWD website...")
        driver.get("https://etender.cpwd.gov.in/")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Check if CAPTCHA is present
        if not headless:
            input("If there's a CAPTCHA, please solve it manually and press Enter to continue...")
        
        # Click on the "New Tenders" tab
        print("Clicking on 'New Tenders' tab...")
        try:
            new_tenders_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'New Tenders')]"))
            )
            new_tenders_tab.click()
        except Exception as e:
            print(f"Error clicking 'New Tenders' tab: {e}")
            print("Trying alternative method...")
            # Try JavaScript click as a fallback
            driver.execute_script("document.querySelector('a:contains(\"New Tenders\")').click();")
        
        # Wait for the page to update
        time.sleep(3)
        
        # Click on the "All" sub-tab
        print("Clicking on 'All' sub-tab...")
        try:
            all_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'All')]"))
            )
            all_tab.click()
        except Exception as e:
            print(f"Error clicking 'All' sub-tab: {e}")
            print("Trying alternative method...")
            # Try JavaScript click as a fallback
            driver.execute_script("document.querySelector('a:contains(\"All\")').click();")
        
        # Wait for the tender list to load
        time.sleep(5)
        
        # Extract data for the first 20 tenders
        print("Extracting tender data...")
        tenders_data = []
        
        # Find all tender rows
        try:
            tender_rows = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//table[@id='tendersTable']/tbody/tr"))
            )
            
            # If no rows found, try alternative selector
            if not tender_rows:
                print("No tender rows found with primary selector, trying alternative...")
                tender_rows = driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
        except Exception as e:
            print(f"Error finding tender rows: {e}")
            print("Taking screenshot for debugging...")
            driver.save_screenshot("debug_screenshot.png")
            print(f"Screenshot saved to {os.path.abspath('debug_screenshot.png')}")
            return []
        
        print(f"Found {len(tender_rows)} tender rows")
        
        # Limit to first 20 rows
        tender_rows = tender_rows[:20] if len(tender_rows) > 20 else tender_rows
        
        for i, row in enumerate(tender_rows):
            print(f"Processing tender {i+1}/{len(tender_rows)}...")
            
            try:
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
                        # Try exact match first
                        field_element = soup.find('td', string=field_name)
                        
                        # If not found, try partial match
                        if not field_element:
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
                try:
                    back_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
                    back_button.click()
                except:
                    print("Back button not found, trying browser back...")
                    driver.back()
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing tender {i+1}: {e}")
                # Try to recover and continue with next tender
                try:
                    driver.back()
                    time.sleep(2)
                except:
                    print("Failed to recover, continuing...")
        
        return tenders_data
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Taking screenshot for debugging...")
        driver.save_screenshot("error_screenshot.png")
        print(f"Screenshot saved to {os.path.abspath('error_screenshot.png')}")
        return []
        
    finally:
        # Close the browser
        driver.quit()

def save_to_csv(data, filename="cpwd_tenders.csv"):
    """Save the scraped data to a CSV file with renamed columns"""
    if not data:
        print("No data to save.")
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
    
    # Rename columns
    df = df.rename(columns=csv_cols)
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    print("Starting CPWD tender scraping...")
    
    # First try in headless mode
    print("Attempting to scrape in headless mode...")
    tenders_data = scrape_cpwd_tenders(headless=True)
    
    # If headless mode fails, try interactive mode
    if not tenders_data:
        print("Headless mode failed. Switching to interactive mode for manual CAPTCHA solving...")
        tenders_data = scrape_cpwd_tenders(headless=False)
    
    if tenders_data:
        print(f"Successfully scraped {len(tenders_data)} tenders.")
        save_to_csv(tenders_data)
    else:
        print("Failed to scrape tender data.")

if __name__ == "__main__":
    main()