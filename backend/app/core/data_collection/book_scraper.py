import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import hashlib
import asyncio
from urllib.parse import urljoin
from pydantic import BaseModel, Field

from .base import BaseCrawler, Document,BaseScraper



class BookScraper(BaseScraper):
    """Scraper for extracting data from books"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sources = config.get('sources', ['gutenberg', 'openlibrary'])
        self.max_books = config.get('max_books', 50)
        
    async def scrape(self, topic: str, limit: int = 100) -> List[Document]:
        """Scrape books based on topic"""
        tasks = []
        
        if 'gutenberg' in self.sources:
            tasks.append(self._scrape_gutenberg(topic, limit))
        if 'openlibrary' in self.sources:
            tasks.append(self._scrape_openlibrary(topic, limit))
            
        results = await asyncio.gather(*tasks)
        
        for result in results:
            self.documents.extend(result)
            
        return self.documents[:limit]
    
    async def _scrape_gutenberg(self, topic: str, limit: int) -> List[Document]:
        """Scrape from Project Gutenberg"""
        documents = []
        search_url = f"https://www.gutenberg.org/ebooks/search/?query={topic.replace(' ', '+')}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract book links
                        book_links = soup.select('.booklink a')[:limit]
                        
                        for link in book_links:
                            book_url = urljoin("https://www.gutenberg.org", link.get('href'))
                            doc = await self._extract_book(session, book_url)
                            if doc and await self.validate(doc):
                                documents.append(doc)
            except Exception as e:
                print(f"Error scraping Gutenberg: {e}")
                
        return documents
    
    async def _scrape_openlibrary(self, topic: str, limit: int) -> List[Document]:
        """Scrape from Open Library"""
        documents = []
        api_url = f"https://openlibrary.org/search.json?q={topic.replace(' ', '+')}&limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for book in data.get('docs', []):
                            doc = await self._process_book_data(book)
                            if doc and await self.validate(doc):
                                documents.append(doc)
            except Exception as e:
                print(f"Error scraping Open Library: {e}")
                
        return documents
    
    async def _extract_book(self, session: aiohttp.ClientSession, url: str) -> Document:
        """Extract book content from URL"""
        async with session.get(url) as response:
            if response.status != 200:
                return None
                
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract book content
            content_div = soup.find('div', {'class': 'book-content'})
            if not content_div:
                content_div = soup.find('pre')
                
            if content_div:
                text = content_div.get_text()
            else:
                text = soup.get_text()
                
            # Generate document ID
            doc_id = hashlib.md5(f"{url}".encode()).hexdigest()
            
            return Document(
                id=doc_id,
                content=text[:10000],  # Limit content length
                metadata={
                    'url': url,
                    'title': soup.title.string if soup.title else '',
                    'source': 'book'
                },
                source='book'
            )
    
    async def _process_book_data(self, book: Dict[str, Any]) -> Document:
        """Process Open Library book data"""
        title = book.get('title', '')
        authors = book.get('author_name', [])
        content = f"Title: {title}\nAuthor: {', '.join(authors)}\n"
        content += f"Subject: {', '.join(book.get('subject', []))}\n"
        content += f"Description: {book.get('description', 'No description available')}"
        
        doc_id = hashlib.md5(f"{title}_{authors}".encode()).hexdigest()
        
        return Document(
            id=doc_id,
            content=content,
            metadata={
                'title': title,
                'authors': authors,
                'first_publish_year': book.get('first_publish_year'),
                'source': 'openlibrary'
            },
            source='book'
        )
    
    async def validate(self, document: Document) -> bool:
        """Validate book document"""
        if len(document.content) < 200:
            return False
        
        # Check for valid content
        if document.content.count('\n') < 3:
            return False
            
        return True