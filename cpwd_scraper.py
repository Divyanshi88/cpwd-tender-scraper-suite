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

def setup_driver():
    """Set up and return a configured Chrome webdriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add user agent to appear more like a regular browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_cpwd_tenders():
    """Scrape tender data from CPWD website"""
    driver = setup_driver()
    
    try:
        # Navigate to the CPWD website
        print("Navigating to CPWD website...")
        driver.get("https://etender.cpwd.gov.in/")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Click on the "New Tenders" tab
        print("Clicking on 'New Tenders' tab...")
        new_tenders_tab = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'New Tenders')]"))
        )
        new_tenders_tab.click()
        
        # Wait for the page to update
        time.sleep(3)
        
        # Click on the "All" sub-tab
        print("Clicking on 'All' sub-tab...")
        all_tab = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'All')]"))
        )
        all_tab.click()
        
        # Wait for the tender list to load
        time.sleep(5)
        
        # Extract data for the first 20 tenders
        print("Extracting tender data...")
        tenders_data = []
        
        # Find all tender rows
        tender_rows = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[@id='tendersTable']/tbody/tr"))
        )
        
        # Limit to first 20 rows
        tender_rows = tender_rows[:20] if len(tender_rows) > 20 else tender_rows
        
        for row in tender_rows:
            # Click on the row to view details
            row.click()
            time.sleep(2)
            
            # Extract the required fields from the tender details
            tender_data = {}
            
            # Extract NIT/RFP NO
            try:
                tender_data["NIT/RFP NO"] = driver.find_element(By.XPATH, "//td[contains(text(), 'NIT/RFP NO')]/following-sibling::td").text.strip()
            except:
                tender_data["NIT/RFP NO"] = "N/A"
            
            # Extract Name of Work / Subwork / Packages
            try:
                tender_data["Name of Work / Subwork / Packages"] = driver.find_element(By.XPATH, "//td[contains(text(), 'Name of Work')]/following-sibling::td").text.strip()
            except:
                tender_data["Name of Work / Subwork / Packages"] = "N/A"
            
            # Extract Estimated Cost
            try:
                tender_data["Estimated Cost"] = driver.find_element(By.XPATH, "//td[contains(text(), 'Estimated Cost')]/following-sibling::td").text.strip()
            except:
                tender_data["Estimated Cost"] = "N/A"
            
            # Extract Bid Submission Closing Date & Time
            try:
                tender_data["Bid Submission Closing Date & Time"] = driver.find_element(By.XPATH, "//td[contains(text(), 'Bid Submission Closing Date')]/following-sibling::td").text.strip()
            except:
                tender_data["Bid Submission Closing Date & Time"] = "N/A"
            
            # Extract EMD Amount
            try:
                tender_data["EMD Amount"] = driver.find_element(By.XPATH, "//td[contains(text(), 'EMD Amount')]/following-sibling::td").text.strip()
            except:
                tender_data["EMD Amount"] = "N/A"
            
            # Extract Bid Opening Date & Time
            try:
                tender_data["Bid Opening Date & Time"] = driver.find_element(By.XPATH, "//td[contains(text(), 'Bid Opening Date')]/following-sibling::td").text.strip()
            except:
                tender_data["Bid Opening Date & Time"] = "N/A"
            
            tenders_data.append(tender_data)
            
            # Go back to the tender list
            back_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
            back_button.click()
            time.sleep(2)
        
        return tenders_data
        
    except Exception as e:
        print(f"An error occurred: {e}")
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
    tenders_data = scrape_cpwd_tenders()
    
    if tenders_data:
        print(f"Successfully scraped {len(tenders_data)} tenders.")
        save_to_csv(tenders_data)
    else:
        print("Failed to scrape tender data.")

if __name__ == "__main__":
    main()