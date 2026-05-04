import os
import zipfile
import time
from typing import Optional
from playwright.sync_api import sync_playwright
from core.utils.logger import get_data_logger

logger = get_data_logger("NseXbrlCollector")

class NseXbrlCollector:
    """
    Automated scraper to pull raw, auditor-signed XBRL XML filings directly from the NSE.
    Bypasses Cloudflare/Akamai WAF by using a headless Chromium browser via Playwright.
    """
    def __init__(self, vault_dir: str = "app/data/xbrl/"):
        self.vault_dir = vault_dir
        os.makedirs(self.vault_dir, exist_ok=True)
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def download_latest_xbrl(self, symbol: str) -> Optional[str]:
        """
        Spawns a headless browser to establish legitimacy, fetches the filing URL,
        downloads the ZIP, unzips it, and returns the path to the XML file.
        """
        logger.info(f"Spawning headless Chromium for {symbol}...")
        
        try:
            with sync_playwright() as p:
                # Force HTTP/1.1 to bypass Cloudflare's HTTP/2 fingerprinting
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-http2',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
                context = browser.new_context(
                    user_agent=self.user_agent,
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
                    }
                )
                page = context.new_page()

                # 1. Establish 'Legitimacy'
                logger.info("Visiting NSE Homepage to establish cookies...")
                # Use 'commit' to return instantly when headers arrive, letting JS challenges run in background
                try:
                    page.goto("https://www.nseindia.com", wait_until="commit", timeout=30000)
                except Exception as e:
                    logger.warning(f"Homepage timeout ignored ({e})")
                time.sleep(5) 

                # 2. Go to the specific Filing API URL
                api_url = f"https://www.nseindia.com/api/corporate-integrated-filing?symbol={symbol}"
                
                logger.info(f"Intercepting API response for {symbol}...")
                
                # We catch the response directly from the browser's network traffic
                with page.expect_response(lambda response: "corporate-integrated-filing" in response.url, timeout=60000) as response_info:
                    page.goto(api_url, wait_until="domcontentloaded", timeout=60000)
                    
                response = response_info.value
                
                if not response.ok:
                    logger.error(f"NSE API Error for {symbol}: HTTP {response.status}")
                    browser.close()
                    return None
                    
                data = response.json()

                # 3. Download the ZIP
                xbrl_url = None
                for filing in data:
                    if filing.get('xbrl_url'):
                        xbrl_url = filing.get('xbrl_url')
                        period = filing.get('period', 'unknown_period')
                        logger.info(f"Found XBRL filing (Period: {period}). Initiating headless download...")
                        break

                if xbrl_url:
                    with page.expect_download() as download_info:
                        page.goto(xbrl_url)
                    download = download_info.value
                    
                    zip_path = os.path.join(self.vault_dir, f"{symbol}_xbrl.zip")
                    download.save_as(zip_path)
                    logger.info(f"Archive Secured: {zip_path}")
                    
                    # 4. Extract to Vault
                    extract_path = os.path.join(self.vault_dir, f"{symbol}_latest")
                    os.makedirs(extract_path, exist_ok=True)
                    
                    with zipfile.ZipFile(zip_path, 'r') as z:
                        z.extractall(extract_path)
                        
                    logger.info(f"Successfully unzipped XBRL for {symbol}")
                    
                    # Find the actual .xml file inside the extracted folder
                    for file in os.listdir(extract_path):
                        if file.endswith(".xml"):
                            full_xml_path = os.path.join(extract_path, file)
                            final_path = os.path.join(self.vault_dir, f"{symbol}_latest.xml")
                            os.rename(full_xml_path, final_path)
                            browser.close()
                            return final_path
                else:
                    logger.warning(f"No XBRL filings found for {symbol} in the intercepted JSON.")
                    
                browser.close()
                return None
                
        except Exception as e:
            logger.error(f"Playwright Error: {e}")
            return None
