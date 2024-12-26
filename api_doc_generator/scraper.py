import httpx
from typing import Set, List, Dict, Optional
import logging
from tqdm import tqdm
import time
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
from bs4 import BeautifulSoup
import re

# Get your Jina AI API key for free: https://jina.ai/?sui=apikey
load_dotenv()
JINA_API_KEY = os.getenv('JINA_API_KEY')

if not JINA_API_KEY:
    raise ValueError("Please set your JINA_API_KEY in the .env file. Get one at https://jina.ai/?sui=apikey")

class JinaAPIError(Exception):
    """Custom exception for Jina AI API errors"""
    pass

class APIScraper:
    def __init__(self, base_url: str):
        """
        Initialize the API documentation scraper using Jina AI APIs
        
        Args:
            base_url (str): The root URL of the API documentation to scrape
        """
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.api_docs: Dict[str, dict] = {}
        self.client = httpx.Client(timeout=30.0)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for Jina AI API requests"""
        return {
            'Authorization': f'Bearer {JINA_API_KEY}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, JinaAPIError))
    )
    def _call_reader_api(self, url: str) -> dict:
        """
        Call Jina AI Reader API with retry logic
        
        Args:
            url (str): URL to scrape
            
        Returns:
            dict: Parsed JSON response from Reader API
            
        Raises:
            JinaAPIError: If the API returns an error response
            httpx.RequestError: For network-related errors
        """
        try:
            response = self.client.post(
                'https://r.jina.ai/',
                headers=self._get_headers(),
                json={
                    'url': url,
                    'with_links_summary': True,
                    'with_images_summary': True
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self.logger.error(f"Reader API error for {url}: {str(e)}")
            raise
        except Exception as e:
            raise JinaAPIError(f"Unexpected error in Reader API: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, JinaAPIError))
    )
    def _segment_content(self, content: str) -> List[str]:
        """
        Segment content using Jina AI Segmenter API
        
        Args:
            content (str): Content to segment
            
        Returns:
            List[str]: List of content chunks
            
        Raises:
            JinaAPIError: If the API returns an error response
            httpx.RequestError: For network-related errors
        """
        try:
            response = self.client.post(
                'https://segment.jina.ai/',
                headers=self._get_headers(),
                json={
                    'content': content,
                    'return_chunks': True,
                    'max_chunk_length': 1000,
                    'chunk_overlap': 100
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get('chunks', [])
        except httpx.RequestError as e:
            self.logger.error(f"Segmenter API error: {str(e)}")
            raise
        except Exception as e:
            raise JinaAPIError(f"Unexpected error in Segmenter API: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, JinaAPIError))
    )
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for text chunks using Jina AI Embeddings API
        
        Args:
            texts (List[str]): List of text chunks to get embeddings for
            
        Returns:
            List[List[float]]: List of embeddings vectors
            
        Raises:
            JinaAPIError: If the API returns an error response
            httpx.RequestError: For network-related errors
        """
        try:
            response = self.client.post(
                'https://api.jina.ai/v1/embeddings',
                headers=self._get_headers(),
                json={
                    'model': 'jina-embeddings-v3',
                    'input': texts
                }
            )
            response.raise_for_status()
            return [item['embedding'] for item in response.json()['data']]
        except httpx.RequestError as e:
            self.logger.error(f"Embeddings API error: {str(e)}")
            raise
        except Exception as e:
            raise JinaAPIError(f"Unexpected error in Embeddings API: {str(e)}")

    def _extract_code_samples(self, content: str) -> List[str]:
        """Extract code samples from content using simple heuristics"""
        # Look for code blocks in markdown and HTML
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
        code_blocks.extend(re.findall(r'<pre><code>(.*?)</code></pre>', content, re.DOTALL))
        
        # Parse HTML content for additional code blocks
        soup = BeautifulSoup(content, 'html.parser')
        for code_elem in soup.find_all(['code', 'pre']):
            if code_elem.text.strip():
                code_blocks.append(code_elem.text.strip())
                
        return [self._clean_code_block(block) for block in code_blocks if block.strip()]

    def _clean_code_block(self, code: str) -> str:
        """Clean a code block by removing unnecessary whitespace and line numbers."""
        if not code:
            return ""
        
        # Remove line number references (e.g., _25, _41, _42, or plain numbers)
        code = re.sub(r'\s*_?\d+\s*$', '', code)  # Remove trailing numbers
        code = re.sub(r'^\s*_?\d+\s*', '', code, flags=re.MULTILINE)  # Remove leading numbers
        code = re.sub(r'\n\s*\n+', '\n\n', code)  # Normalize multiple newlines
        
        # Remove leading/trailing whitespace while preserving indentation
        lines = code.splitlines()
        # Remove empty lines from start and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
            
        if not lines:
            return ""
            
        # Find minimum indentation (excluding empty lines)
        min_indent = min(len(line) - len(line.lstrip()) 
                        for line in lines if line.strip())
        
        # Remove minimum indentation from all lines
        cleaned_lines = [line[min_indent:] if line.strip() else '' 
                        for line in lines]
        
        return '\n'.join(cleaned_lines).strip()

    def _clean_html(self, content: str) -> str:
        """Clean HTML content and extract meaningful text"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
            
        # Get text and preserve some structure
        lines = []
        for elem in soup.stripped_strings:
            line = elem.strip()
            if line:
                lines.append(line)
                
        return '\n'.join(lines)

    def scrape_page(self, url: str) -> List[str]:
        """
        Scrape a single page using Jina AI Reader API
        
        Args:
            url (str): URL to scrape
            
        Returns:
            List[str]: List of discovered URLs
            
        Raises:
            JinaAPIError: If any Jina API returns an error response
        """
        if url in self.visited_urls:
            return []
            
        self.visited_urls.add(url)
        discovered_urls = []
        
        try:
            # Use Jina AI Reader API to get page content
            reader_response = self._call_reader_api(url)
            content = reader_response['data']['content']
            
            # Clean HTML content
            cleaned_content = self._clean_html(content)
            
            # Extract links and metadata
            links = reader_response['data'].get('links', {})
            title = reader_response['data'].get('title', '')
            description = reader_response['data'].get('description', '')
            
            # Extract code samples
            code_samples = self._extract_code_samples(content)
            
            # Segment content into chunks
            chunks = self._segment_content(cleaned_content)
            
            # Get embeddings for chunks
            embeddings = self._get_embeddings(chunks) if chunks else []
            
            # Store API documentation information
            api_info = {
                'title': title,
                'description': description,
                'content': cleaned_content,
                'raw_content': content,
                'chunks': chunks,
                'embeddings': embeddings,
                'code_samples': code_samples,
                'links': links,
                'url': url,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.api_docs[url] = api_info
            
            # Add discovered URLs
            discovered_urls.extend([url for url in links.values() if self.is_valid_url(url)])
                    
        except (JinaAPIError, httpx.RequestError) as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            
        return discovered_urls

    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL belongs to the same domain as base_url
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL is valid and belongs to same domain
        """
        from urllib.parse import urlparse
        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain in url_domain

    def crawl(self) -> Dict[str, dict]:
        """
        Start the crawling process from the base URL using Jina AI APIs
        
        Returns:
            Dict[str, dict]: Collected API documentation
            
        Example:
            >>> scraper = APIScraper("https://docs.example.com/api")
            >>> docs = scraper.crawl()
            >>> print(f"Scraped {len(docs)} pages")
        """
        urls_to_visit = [self.base_url]
        
        with tqdm(desc="Crawling pages", unit="page") as pbar:
            while urls_to_visit:
                # Respect rate limits
                time.sleep(0.3)  # ~200 requests per minute
                
                url = urls_to_visit.pop(0)
                new_urls = self.scrape_page(url)
                urls_to_visit.extend(new_urls)
                pbar.update(1)
                
        self.logger.info(f"Crawling completed. Processed {len(self.visited_urls)} pages.")
        return self.api_docs
