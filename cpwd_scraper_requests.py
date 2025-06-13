import requests
import pandas as pd
import logging
import time
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin

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

def scrape_cpwd_tenders():
    """
    Scrape tender data from CPWD website using requests and BeautifulSoup
    
    Returns:
        list: List of dictionaries containing tender data
    """
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
            return []
        
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
            return []
        
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
        
        # If we couldn't find data in tables, try to look for tender links
        if not tenders_data:
            logger.info("No data found in tables, looking for tender links")
            
            # Look for links that might point to tender details
            tender_links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and ('tender' in href.lower() or 'nit' in href.lower()):
                    tender_links.append(href)
            
            logger.info(f"Found {len(tender_links)} potential tender links")
            
            # Process up to 20 links
            for i, link in enumerate(tender_links[:20]):
                try:
                    logger.info(f"Processing tender link {i+1}: {link}")
                    
                    # Navigate to the tender details page
                    tender_url = urljoin(base_url, link)
                    response = session.get(tender_url)
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to access tender details: {response.status_code}")
                        continue
                    
                    # Parse the tender details page
                    details_soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract tender data
                    tender_data = {}
                    
                    # Function to extract field data
                    def extract_field(field_labels):
                        for label in field_labels:
                            try:
                                # Try exact match first
                                field_element = details_soup.find('td', string=label)
                                
                                # If not found, try partial match
                                if not field_element:
                                    field_element = details_soup.find('td', string=lambda text: label in text if text else False)
                                    
                                if field_element:
                                    value = field_element.find_next_sibling('td').get_text(strip=True)
                                    return value
                            except:
                                continue
                        return "N/A"
                    
                    # Define field mappings with multiple possible labels
                    field_mappings = {
                        "NIT/RFP NO": ["NIT/RFP NO", "NIT Number", "Tender Number", "Reference No"],
                        "Name of Work / Subwork / Packages": ["Name of Work", "Work Description", "Title", "Project Name"],
                        "Estimated Cost": ["Estimated Cost", "Tender Value", "Project Cost", "Estimated Value"],
                        "Bid Submission Closing Date & Time": ["Bid Submission Closing Date", "Closing Date", "Submission Deadline"],
                        "EMD Amount": ["EMD Amount", "Earnest Money Deposit", "EMD Value"],
                        "Bid Opening Date & Time": ["Bid Opening Date", "Opening Date", "Tender Opening Date"]
                    }
                    
                    # Extract all required fields
                    for field_key, possible_labels in field_mappings.items():
                        tender_data[field_key] = extract_field(possible_labels)
                    
                    tenders_data.append(tender_data)
                    logger.info(f"Extracted data for tender {i+1}")
                    
                    # Add a small delay to avoid overloading the server
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing tender link {i+1}: {e}")
        
        # If we still don't have data, try to look for JSON data in the page
        if not tenders_data:
            logger.info("No data found in tables or links, looking for JSON data")
            
            # Look for JSON data in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for JSON objects that might contain tender data
                    json_matches = re.findall(r'var\s+(\w+)\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                    for var_name, json_str in json_matches:
                        try:
                            data = json.loads(json_str)
                            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                                logger.info(f"Found potential JSON data: {var_name} with {len(data)} items")
                                
                                # Check if this looks like tender data
                                sample = data[0]
                                relevant_keys = ['nit', 'tender', 'work', 'cost', 'emd', 'date']
                                key_relevance = sum(1 for key in sample.keys() for keyword in relevant_keys if keyword.lower() in key.lower())
                                
                                if key_relevance >= 2:  # At least 2 relevant keys
                                    logger.info("Found relevant tender JSON data")
                                    
                                    # Map JSON keys to our required fields
                                    for item in data[:20]:  # Limit to 20 items
                                        tender_data = {}
                                        
                                        # Try to map JSON keys to our required fields
                                        for key, value in item.items():
                                            key_lower = key.lower()
                                            if any(keyword in key_lower for keyword in ['nit', 'rfp', 'tender', 'reference']):
                                                tender_data["NIT/RFP NO"] = str(value)
                                            elif any(keyword in key_lower for keyword in ['work', 'title', 'project', 'name']):
                                                tender_data["Name of Work / Subwork / Packages"] = str(value)
                                            elif any(keyword in key_lower for keyword in ['cost', 'value', 'amount']) and 'emd' not in key_lower:
                                                tender_data["Estimated Cost"] = str(value)
                                            elif any(keyword in key_lower for keyword in ['closing', 'submission', 'end']):
                                                tender_data["Bid Submission Closing Date & Time"] = str(value)
                                            elif 'emd' in key_lower:
                                                tender_data["EMD Amount"] = str(value)
                                            elif any(keyword in key_lower for keyword in ['opening', 'open']):
                                                tender_data["Bid Opening Date & Time"] = str(value)
                                        
                                        # Ensure all required fields exist
                                        for field in ["NIT/RFP NO", "Name of Work / Subwork / Packages", "Estimated Cost", 
                                                     "Bid Submission Closing Date & Time", "EMD Amount", "Bid Opening Date & Time"]:
                                            if field not in tender_data:
                                                tender_data[field] = "N/A"
                                        
                                        tenders_data.append(tender_data)
                                    
                                    if tenders_data:
                                        break  # Stop processing scripts if we found data
                        except:
                            pass  # Not valid JSON or not relevant data
                
                if tenders_data:
                    break  # Stop processing scripts if we found data
        
        return tenders_data
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []

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
    
    tenders_data = scrape_cpwd_tenders()
    
    if tenders_data:
        logger.info(f"Successfully scraped {len(tenders_data)} tenders.")
        save_to_csv(tenders_data)
    else:
        logger.error("Failed to scrape tender data.")
        
        # Create a sample CSV with dummy data as a fallback
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
        save_to_csv(dummy_data, "cpwd_tenders_sample.csv")
        logger.info("Sample CSV created. Please note this contains DUMMY DATA for demonstration purposes only.")

if __name__ == "__main__":
    main()