
import os
import json
import logging
import re
from typing import List, Dict, Optional
from firecrawl import FirecrawlApp
from urllib.parse import urlparse
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCRAPE_DIR = "scraped_content"

mcp = FastMCP("llm_inference")


def _safe_filename_component(value: str) -> str:
    """Strip path separators/traversal sequences so a caller-supplied name is safe to use in a filename."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', value) or "unnamed"


@mcp.tool()
def scrape_websites(
    websites: Dict[str, str],
    formats: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> List[str]:
    """
    Scrape multiple websites using Firecrawl and store their content.
    
    Args:
        websites: Dictionary of provider_name -> URL mappings
        formats: List of formats to scrape ['markdown', 'html'] (default: both)
        api_key: Firecrawl API key (if None, expects environment variable)
        
    Returns:
        List of provider names for successfully scraped websites
    """
    
    if formats is None:
        formats = ['markdown', 'html']

    if api_key is None:
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            raise ValueError("API key must be provided or set as FIRECRAWL_API_KEY environment variable")
    
    app = FirecrawlApp(api_key=api_key)
    
    path = os.path.join(SCRAPE_DIR)
    os.makedirs(path, exist_ok=True)
    
    # save the scraped content to files and then create scraped_metadata.json as a summary file
    # check if the provider has already been scraped and decide if you want to overwrite
    # {
    #     "cloudrift_ai": {
    #         "provider_name": "cloudrift_ai",
    #         "url": "https://www.cloudrift.ai/inference",
    #         "domain": "www.cloudrift.ai",
    #         "scraped_at": "2025-10-23T00:44:59.902569",
    #         "formats": [
    #             "markdown",
    #             "html"
    #         ],
    #         "success": "true",
    #         "content_files": {
    #             "markdown": "cloudrift_ai_markdown.txt",
    #             "html": "cloudrift_ai_html.txt"
    #         },
    #         "title": "AI Inference",
    #         "description": "Scraped content goes here"
    #     }
    # }
    metadata_file = os.path.join(path, "scraped_metadata.json")

    try:
        with open(metadata_file, 'r') as f:
            scraped_metadata = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        scraped_metadata = {}

    successful_scrapes = []

    for provider_name, url in websites.items():
        try:
            logger.info(f"Scraping {provider_name}: {url}")

            scrape_result = app.scrape(url, formats=formats).model_dump()

            # firecrawl-py v2's scrape() returns the Document directly (no 'success'
            # wrapper) and raises on failure, so treat a returned page_metadata error as the failure signal.
            page_metadata = scrape_result.get('metadata') or {}
            success = scrape_result.get('success', True) and not page_metadata.get('error')

            metadata = {
                "provider_name": provider_name,
                "url": url,
                "domain": urlparse(url).netloc,
                "scraped_at": datetime.now().isoformat(),
                "formats": formats,
                "success": success,
            }

            if success:
                content_files = {}
                for format_type in formats:
                    content = scrape_result.get(format_type)
                    if content is None:
                        continue
                    filename = f"{_safe_filename_component(provider_name)}_{_safe_filename_component(format_type)}.txt"
                    file_path = os.path.join(path, filename)
                    with open(file_path, 'w') as f:
                        f.write(content)
                    content_files[format_type] = filename

                metadata["content_files"] = content_files
                metadata["title"] = page_metadata.get('title', '')
                metadata["description"] = page_metadata.get('description', '')

                successful_scrapes.append(provider_name)
            else:
                logger.error(f"Failed to scrape {provider_name}: {page_metadata.get('error') or scrape_result.get('error')}")

            scraped_metadata[provider_name] = metadata

        except Exception as e:
            logger.error(f"Error scraping {provider_name}: {e}")
            scraped_metadata[provider_name] = {
                "provider_name": provider_name,
                "url": url,
                "domain": urlparse(url).netloc,
                "scraped_at": datetime.now().isoformat(),
                "formats": formats,
                "success": False,
                "error": str(e),
            }

    with open(metadata_file, 'w') as f:
        json.dump(scraped_metadata, f, indent=2)

    logger.info(f"Successfully scraped {len(successful_scrapes)} out of {len(websites)} websites")

    return successful_scrapes

@mcp.tool()
def extract_scraped_info(identifier: str) -> str:
    """
    Extract information about a scraped website.
    
    Args:
        identifier: The provider name, full URL, or domain to look for
        
    Returns:
        Formatted JSON string with the scraped information
    """
    
    logger.info(f"Extracting information for identifier: {identifier}")
    if os.path.isdir(SCRAPE_DIR):
        logger.info(f"Files in {SCRAPE_DIR}: {os.listdir(SCRAPE_DIR)}")
    else:
        logger.info(f"{SCRAPE_DIR} does not exist yet")

    metadata_file = os.path.join(SCRAPE_DIR, "scraped_metadata.json")
    logger.info(f"Checking metadata file: {metadata_file}")

    try:
        with open(metadata_file, 'r') as f:
            scraped_metadata = json.load(f)

        for provider_name, metadata in scraped_metadata.items():
            if identifier in (provider_name, metadata.get('url', ''), metadata.get('domain', '')):
                result = metadata.copy()

                if 'content_files' in metadata:
                    result['content'] = {}
                    for format_type, filename in metadata['content_files'].items():
                        file_path = os.path.join(SCRAPE_DIR, filename)
                        with open(file_path, 'r') as content_file:
                            result['content'][format_type] = content_file.read()

                return json.dumps(result, indent=2)

        return f"There's no saved information related to identifier '{identifier}'."

    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.error(f"Error reading scraped info: {e}")
        return f"There's no saved information related to identifier '{identifier}'."

if __name__ == "__main__":
    mcp.run(transport="stdio")