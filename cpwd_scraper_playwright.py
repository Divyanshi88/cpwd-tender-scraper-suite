import asyncio
import pandas as pd
import logging
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

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

async def scrape_cpwd_tenders(headless=True):
    """
    Scrape tender data from CPWD website using Playwright
    
    Args:
        headless (bool): Whether to run in headless mode
    
    Returns:
        list: List of dictionaries containing tender data
    """
    async with async_playwright() as p:
        browser = None
        try:
            # Launch browser
            browser = await p.chromium.launch(headless=headless)
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
            
            # Check if CAPTCHA is present and handle it if in interactive mode
            if not headless:
                input("If there's a CAPTCHA, please solve it manually and press Enter to continue...")
            
            # Take a screenshot of the initial page
            await page.screenshot(path="initial_page.png")
            logger.info(f"Screenshot saved to {os.path.abspath('initial_page.png')}")
            
            # Click on the "New Tenders" tab with multiple strategies
            logger.info("Clicking on 'New Tenders' tab...")
            new_tenders_selectors = [
                "text=New Tenders",
                "a:has-text('New Tenders')",
                "a[href*='new-tenders']"
            ]
            
            clicked = False
            for selector in new_tenders_selectors:
                try:
                    logger.info(f"Trying to click element with selector: {selector}")
                    await page.click(selector)
                    clicked = True
                    logger.info(f"Successfully clicked element with selector: {selector}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to click element with selector {selector}: {e}")
            
            if not clicked:
                # Try direct navigation as a last resort
                logger.info("Trying direct navigation to New Tenders page...")
                await page.goto("https://etender.cpwd.gov.in/new-tenders")
            
            # Wait for the page to update
            await page.wait_for_timeout(3000)
            
            # Click on the "All" sub-tab with multiple strategies
            logger.info("Clicking on 'All' sub-tab...")
            all_tab_selectors = [
                "text=All",
                "a:has-text('All')",
                "ul.nav-tabs li a"
            ]
            
            clicked = False
            for selector in all_tab_selectors:
                try:
                    logger.info(f"Trying to click element with selector: {selector}")
                    await page.click(selector)
                    clicked = True
                    logger.info(f"Successfully clicked element with selector: {selector}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to click element with selector {selector}: {e}")
            
            # Wait for the tender list to load
            await page.wait_for_timeout(5000)
            
            # Take a screenshot of the tender list
            await page.screenshot(path="tender_list.png")
            logger.info(f"Screenshot saved to {os.path.abspath('tender_list.png')}")
            
            # Extract data for the first 20 tenders
            logger.info("Extracting tender data...")
            tenders_data = []
            
            # Get the page content and parse with BeautifulSoup
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try multiple strategies to find tender rows
            tender_rows = []
            
            # Try to find table rows
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables on the page")
            
            if tables:
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 1:  # At least one header row and one data row
                        logger.info(f"Found table with {len(rows)} rows")
                        # Skip header row
                        tender_rows = rows[1:]
                        break
            
            if not tender_rows:
                logger.error("Could not find any tender rows")
                return []
            
            # Limit to first 20 rows
            tender_rows = tender_rows[:20] if len(tender_rows) > 20 else tender_rows
            
            for i, row in enumerate(tender_rows):
                logger.info(f"Processing tender {i+1}/{len(tender_rows)}...")
                
                try:
                    # Find all cells in the row
                    cells = row.find_all('td')
                    
                    # Extract data from the row
                    tender_data = {}
                    
                    # Try to determine which columns contain our required data
                    # This is a simplified approach - in a real scenario, we'd need to analyze the table headers
                    
                    # Assuming a typical structure where:
                    # - First column might be NIT/RFP NO
                    # - Second column might be Name of Work
                    # - There might be columns for dates, costs, etc.
                    
                    if len(cells) >= 1:
                        tender_data["NIT/RFP NO"] = cells[0].get_text(strip=True)
                    else:
                        tender_data["NIT/RFP NO"] = "N/A"
                        
                    if len(cells) >= 2:
                        tender_data["Name of Work / Subwork / Packages"] = cells[1].get_text(strip=True)
                    else:
                        tender_data["Name of Work / Subwork / Packages"] = "N/A"
                    
                    # For the remaining fields, we'll need to click on the row to view details
                    # Find a clickable element in the row
                    links = row.find_all('a')
                    if links:
                        # Get the href attribute
                        href = links[0].get('href')
                        if href:
                            logger.info(f"Clicking link: {href}")
                            # Navigate to the details page
                            await page.goto(f"https://etender.cpwd.gov.in{href}" if href.startswith('/') else href)
                            await page.wait_for_timeout(2000)
                            
                            # Take a screenshot of the details page
                            await page.screenshot(path=f"tender_details_{i+1}.png")
                            
                            # Get the details page content
                            details_content = await page.content()
                            details_soup = BeautifulSoup(details_content, 'html.parser')
                            
                            # Extract the required fields from the tender details
                            def extract_field(field_name):
                                try:
                                    field_element = details_soup.find('td', string=lambda text: field_name in text if text else False)
                                    if field_element:
                                        value = field_element.find_next_sibling('td').get_text(strip=True)
                                        return value
                                    return "N/A"
                                except:
                                    return "N/A"
                            
                            # Extract remaining fields
                            tender_data["Estimated Cost"] = extract_field("Estimated Cost")
                            tender_data["Bid Submission Closing Date & Time"] = extract_field("Bid Submission Closing Date")
                            tender_data["EMD Amount"] = extract_field("EMD Amount")
                            tender_data["Bid Opening Date & Time"] = extract_field("Bid Opening Date")
                            
                            # Go back to the tender list
                            await page.go_back()
                            await page.wait_for_timeout(2000)
                    else:
                        # If we can't click to get details, set default values
                        tender_data["Estimated Cost"] = "N/A"
                        tender_data["Bid Submission Closing Date & Time"] = "N/A"
                        tender_data["EMD Amount"] = "N/A"
                        tender_data["Bid Opening Date & Time"] = "N/A"
                    
                    tenders_data.append(tender_data)
                    logger.info(f"Successfully extracted data for tender {i+1}")
                    
                except Exception as e:
                    logger.error(f"Error processing tender {i+1}: {e}")
                    # Try to recover and continue with next tender
                    try:
                        await page.go_back()
                        await page.wait_for_timeout(2000)
                    except:
                        logger.error("Failed to recover, continuing...")
            
            return tenders_data
            
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            if browser:
                # Take a screenshot for debugging
                page = await browser.new_page()
                await page.screenshot(path="error_screenshot.png")
                logger.info(f"Screenshot saved to {os.path.abspath('error_screenshot.png')}")
            return []
            
        finally:
            # Close the browser
            if browser:
                await browser.close()

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

async def main():
    logger.info("Starting CPWD tender scraping...")
    
    # First try in headless mode
    logger.info("Attempting to scrape in headless mode...")
    tenders_data = await scrape_cpwd_tenders(headless=True)
    
    # If headless mode fails or returns insufficient data, try interactive mode
    if not tenders_data or len(tenders_data) < 5:  # Arbitrary threshold
        logger.info("Headless mode failed or returned insufficient data. Switching to interactive mode...")
        tenders_data = await scrape_cpwd_tenders(headless=False)
    
    if tenders_data:
        logger.info(f"Successfully scraped {len(tenders_data)} tenders.")
        save_to_csv(tenders_data)
    else:
        logger.error("Failed to scrape tender data.")

if __name__ == "__main__":
    asyncio.run(main())