from typing import Dict, Any
from .base import BaseCrawler
from .web_scraper import WebScraper
from .book_crawler import BookCrawler

class CrawlerFactory:
    """Factory pattern for creating crawlers"""
    
    _crawlers = {
        'web': WebScraper,
        'book': BookCrawler
    }
    
    @classmethod
    def get_crawler(cls, crawler_type: str, config: Dict[str, Any]) -> BaseCrawler:
        """Get crawler instance by type"""
        crawler_class = cls._crawlers.get(crawler_type)
        if not crawler_class:
            raise ValueError(f"Unknown crawler type: {crawler_type}")
        return crawler_class(config)
    
    @classmethod
    def register_crawler(cls, name: str, crawler_class):
        """Register new crawler type"""
        cls._crawlers[name] = crawler_class