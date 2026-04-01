import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import hashlib
from concurrent.futures import ProcessPoolExecutor
from pydantic import BaseModel, Field
from urllib.parse import urljoin, urlparse, quote
import asyncio
from datetime import datetime, timedelta
import random
from .base import BaseCrawler, Document, BaseScraper

class RateLimiter:
    """Simple rate limiter to avoid being blocked"""
    
    def __init__(self, requests_per_second: float = 5):
        self.requests_per_second = requests_per_second
        self.last_request_time = None
        self.min_interval = 1.0 / requests_per_second
    
    async def wait_if_needed(self):
        """Wait if needed to respect rate limit"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
        
        self.last_request_time = datetime.now()



class WebScraper(BaseScraper):
    """Web scraper implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.user_agent = config.get('user_agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36')
        self.timeout = config.get('timeout', 10)
        self.max_depth = config.get('max_depth', 2)
        self.search_engine = config.get('search_engine', 'google')  # google, bing, duckduckgo, wikipedia
        self.api_keys = config.get('api_keys', {})  # For paid APIs like Google Custom Search
        self.rate_limiter = RateLimiter(requests_per_second=config.get('requests_per_second', 5))
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    async def scrape(self, topic: str, num_workers: int = 2, save: bool = True):
        search_urls = await self._get_search_urls(topic, self.headers, self.timeout)
        search_urls = list(set(search_urls))[:self.config.get('max_search_results', num_workers)]  # Remove duplicates

        if not search_urls:
            raise ValueError("No search results found for the given topic") 

        # Prepare arguments that need to be passed to each process
        # We pass headers and timeout because 'self' isn't available in the worker
        scraper_args = {
            'timeout': self.timeout,
            'headers': self.headers
        }

        # Split URLs into chunks
        chunk_size = (len(search_urls) + num_workers - 1) // num_workers
        chunks = [search_urls[i:i + chunk_size] for i in range(0, len(search_urls), chunk_size)]

        loop = asyncio.get_running_loop()
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor, 
                    WebScraper.run_worker_sync, 
                    chunk, 
                    topic, 
                    scraper_args
                )
                for chunk in chunks
            ]
            
            worker_results = await asyncio.gather(*tasks)
            
        flat_results = [doc for sublist in worker_results for doc in sublist]
        self.documents.extend(flat_results)
        print(f"Scraping completed. Total documents collected: {len(flat_results)}")
        if save:
            self.save_documents(f"scraped_{topic.replace(' ', '_')}.json")
       

    @staticmethod
    def run_worker_sync(urls: List[str], topic: str, config_args: Dict):
        """The entry point for the new process"""
        return asyncio.run(WebScraper.scrape_urls(urls, topic, config_args))

    @staticmethod
    async def scrape_urls(urls: List[str], topic: str, config_args: Dict) -> List[Document]:
        """The async loop inside the child process"""
        documents = []
        # Extract config passed from main process
        timeout = aiohttp.ClientTimeout(total=config_args.get('timeout', 10))
        headers = config_args.get('headers')

        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    # Pass the required headers/timeout to the static scrape_url
                    doc = await WebScraper.scrape_url(session, url, topic, timeout, headers)  # type: ignore
                    print(f"Scraped {url} - Content length: {len(doc.content) if doc else 'N/A'}")
                    if doc and await WebScraper.validate(doc):
                        print(f"Validated document from {url} - Length: {len(doc.content)}")
                        print(f"Metadata: {doc.metadata}")
                        documents.append(doc)
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
        return documents

    @staticmethod
    async def scrape_url(session, url, topic, timeout, headers) -> Document | None:
        async with session.get(url, timeout=timeout, headers=headers) as response:
            if response.status != 200:
                return None
                
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
                
            # FIX: Ensure this is a standard string
            raw_text = soup.get_text()
            lines = (line.strip() for line in raw_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = str(' '.join(chunk for chunk in chunks if chunk)) # Cast to str
            
            # FIX: Ensure title is a standard string, not a NavigableString
            title = str(soup.title.string) if (soup.title and soup.title.string) else ''
            
            doc_id = hashlib.md5(f"{url}_{topic}".encode()).hexdigest()
            
            return Document(
                id=doc_id,
                content=text,
                metadata={
                    'url': str(url),
                    'topic': str(topic),
                    'title': title
                },
                source='web'
            )
        
    @staticmethod
    async def validate(document: Document) -> bool:
        """Validate document quality"""
        # Check minimum content length
        if len(document.content) < 100:
            print(f"Document from {document.metadata['url']} rejected for low content length")
            return False
        
            
        return True
      
    async def _get_search_urls(self, topic: str,*args) -> List[str]:
        """Get URLs from multiple search engines"""
        urls = []

        # return [
        #     f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
        #     f"https://www.google.com/search?q={topic}"
        # ]
    
        
        # Try multiple search engines based on configuration
        if self.search_engine == 'google':
            urls = await self._search_google(topic)
        elif self.search_engine == 'bing':
            urls = await self._search_bing(topic)
        elif self.search_engine == 'duckduckgo':
            urls = await self._search_duckduckgo(topic)
        elif self.search_engine == 'wikipedia':
            urls = await self._search_wikipedia(topic, *args)
        elif self.search_engine == 'academic':
            urls = await self._search_academic(topic)  # ArXiv, PubMed, etc.
        else:
            # Try all search engines
            urls = await self._search_multiple_engines(topic)
        
        # Add fallback URLs if no results
        if not urls:
            print("No search results found, using fallback URLs")
            urls = await self._get_fallback_urls(topic)
        
        # Filter and validate URLs
        urls = await self._filter_urls(urls, topic)
        
        return urls[:self.config.get('max_search_results', 50)]
    
    async def _search_google(self, topic: str) -> List[str]:
        """Search using Google Custom Search API or web scraping"""
        urls = []
        
        # Method 1: Use Google Custom Search API (requires API key)
        if self.api_keys.get('google_cx') and self.api_keys.get('google_api_key'):
            urls = await self._search_google_api(topic, limit=self.config.get('max_search_results', 50))
        
        # Method 2: Fallback to web scraping
        if not urls:
            urls = await self._search_google_scrape(topic)
        
        return urls
    
    async def _search_google_api(self, topic: str, limit: int = 10) -> List[str]:
        """Use Google Custom Search JSON API"""
        try:
            api_key = self.api_keys['google_api_key']
            cx = self.api_keys['google_cx']
            query = quote(topic)
            url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}&num={limit}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        urls = [item['link'] for item in data.get('items', [])]
                        return urls
        except Exception as e:
            print(f"Google API search failed: {e}")
        
        return []
    
    async def _search_google_scrape(self, topic: str) -> List[str]:
        """Scrape Google search results (may be blocked)"""
        urls = []
      
        query = quote(topic)
        search_url = f"https://www.google.com/search?q={query}&num=20"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract search result links
                        for link in soup.find_all('a'):
                            href = link.get('href', '')
                            if href.startswith('/url?q='):
                                url = href.split('/url?q=')[1].split('&')[0]
                                if url.startswith('http') and 'google.com' not in url:
                                    urls.append(url)
        except Exception as e:
            print(f"Google scrape failed: {e}")
        
        return urls
    
    async def _search_bing(self, topic: str) -> List[str]:
        """Search using Bing"""
        urls = []
        headers = {'User-Agent': self.user_agent}
        query = quote(topic)
        search_url = f"https://www.bing.com/search?q={query}&count=20"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract Bing search results
                        for link in soup.find_all('a', {'class': 'tilk'}):
                            href = link.get('href', '')
                            if href.startswith('http'):
                                urls.append(href)
                        
                        # Alternative selector
                        for link in soup.select('li.b_algo h2 a'):
                            href = link.get('href', '')
                            if href.startswith('http'):
                                urls.append(href)
        except Exception as e:
            print(f"Bing search failed: {e}")
        
        return urls
    
    async def _search_duckduckgo(self, topic: str) -> List[str]:
        """Search using DuckDuckGo (privacy-focused)"""
        urls = []
        headers = {'User-Agent': self.user_agent}
        query = quote(topic)
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract DuckDuckGo results
                        for link in soup.find_all('a', {'class': 'result__a'}):
                            href = link.get('href', '')
                            if href.startswith('//'):
                                href = 'https:' + href
                            if href.startswith('http'):
                                urls.append(href)
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
        
        return urls
    
    async def _search_wikipedia(self, topic: str, *args, **kwargs) -> List[str]:
        """Search Wikipedia articles"""
        print(f"Searching Wikipedia for topic: {topic}")
        urls = []
        base_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': topic,
            'format': 'json',
            'srlimit': 20
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=self.timeout, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for result in data.get('query', {}).get('search', []):
                            title = result['title'].replace(' ', '_')
                            url = f"https://en.wikipedia.org/wiki/{quote(title)}"
                            urls.append(url)
        except Exception as e:
            print(f"Wikipedia search failed: {e}")
        
        return urls
    
    async def _search_academic(self, topic: str, *args, **kwargs) -> List[str]:
        """Search academic sources (ArXiv, PubMed, etc.)"""
        urls = []
        
        # Search ArXiv
        arxiv_urls = await self._search_arxiv(topic, *args, **kwargs)
        urls.extend(arxiv_urls)
        
        # Search PubMed
        pubmed_urls = await self._search_pubmed(topic, *args, **kwargs)
        urls.extend(pubmed_urls)
        
        return urls
    
    async def _search_arxiv(self, topic: str, *args, **kwargs) -> List[str]:
        """Search ArXiv for academic papers"""
        urls = []
        base_url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{topic}',
            'start': 0,
            'max_results': 10
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=self.timeout, headers=self.headers) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'xml')
                        for entry in soup.find_all('entry'):
                            link = entry.find('id')
                            if link:
                                urls.append(link.text)
        except Exception as e:
            print(f"ArXiv search failed: {e}")
        
        return urls
    
    async def _search_pubmed(self, topic: str, *args, **kwargs) -> List[str]:
        """Search PubMed for medical/scientific papers"""
        urls = []
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': topic,
            'retmax': 10,
            'format': 'json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=self.timeout, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        ids = data.get('esearchresult', {}).get('idlist', [])
                        for pmid in ids:
                            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            urls.append(url)
        except Exception as e:
            print(f"PubMed search failed: {e}")
        
        return urls
    
    async def _search_multiple_engines(self, topic: str, *args, **kwargs) -> List[str]:
        """Search multiple engines in parallel for comprehensive results"""
        engines = [
            self._search_google,
            self._search_bing,
            self._search_duckduckgo,
            self._search_wikipedia,
            self._search_academic
        ]
        
        tasks = [engine(topic) for engine in engines]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        urls = []
        for result in results:
            if isinstance(result, list):
                urls.extend(result)
        
        # Remove duplicates
        urls = list(dict.fromkeys(urls))
        return urls
    
    async def _get_fallback_urls(self, topic: str) -> List[str]:
        """Get fallback URLs when search engines fail"""
        fallback_urls = [
            f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
            f"https://www.britannica.com/topic/{topic.replace(' ', '-')}",
            f"https://arxiv.org/search/?query={quote(topic)}&searchtype=all",
            f"https://scholar.google.com/scholar?q={quote(topic)}"
        ]
        return fallback_urls
    
    async def _filter_urls(self, urls: List[str], topic: str) -> List[str]:
        """Filter and validate URLs"""
        filtered_urls = []
        
        # Domains to exclude (spam, social media, etc.)
        exclude_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 'reddit.com',
            'pinterest.com', 'tumblr.com', 'linkedin.com', 'youtube.com',
            'amazon.com', 'ebay.com', 'aliexpress.com', 'walmart.com'
        ]
        
        # File extensions to exclude
        exclude_extensions = ['.pdf', '.jpg', '.png', '.gif', '.mp4', '.zip', '.exe']
        
        for url in urls:
            # Check if URL is valid
            if not url or not url.startswith('http'):
                continue
            
            # Check domain exclusion
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if any(exclude in domain for exclude in exclude_domains):
                continue
            
            # Check file extension
            if any(url.lower().endswith(ext) for ext in exclude_extensions):
                continue
            
            # Check if URL is relevant to topic (simple keyword check)
            if topic.lower() in url.lower() or any(
                keyword in url.lower() for keyword in topic.lower().split()
            ):
                filtered_urls.append(url)
            else:
                # Still include but with lower priority
                filtered_urls.append(url)
        
        return filtered_urls
    
    async def _get_related_searches(self, topic: str) -> List[str]:
        """Get related search terms for broader coverage"""
        related_terms = [topic]
        
        # Use Wikipedia to get related topics
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(topic)}&limit=5&namespace=0&format=json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(wiki_url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if len(data) > 1:
                            related_terms.extend(data[1][1:5])  # Get related search suggestions
        except Exception:
            pass
        
        return related_terms
    
def main():
    # Example Config
    config = {
        'timeout': 15,
        'requests_per_second': 2,
        'max_search_results': 10,
        'search_engine': 'wikipedia'
    }
    
    scraper = WebScraper(config)
    
    # This now uses the Multi-CPU logic
    print("Starting parallel scrape...")
    res = asyncio.run(scraper.scrape("Artificial Intelligence", num_workers=2))
    
    print(f"\n--- Results ---")
    for d in res[:3]:
        print(f"Source: {d.metadata['url']} | Length: {len(d.content)}")

if __name__ == "__main__":
    main()
    