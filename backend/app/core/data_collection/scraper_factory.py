from typing import Dict, Any

from pydantic import BaseModel, ConfigDict
from .base import BaseConfig, BaseCrawler,BaseScraper
from .web_scraper import WebScraper
from .book_scraper import BookScraper

class ScraperFactory:
    """Factory pattern for creating scrapers"""
    
    _scrapers = {
        'web': WebScraper,
        'book': BookScraper,
        'upload': BaseScraper  # Placeholder for file upload scraper
    }
    
    @classmethod
    def get_scraper(cls, scraper_type: str, config: BaseConfig) -> BaseScraper:
        """Get scraper instance by type"""
        scraper_class = cls._scrapers.get(scraper_type)
        if not scraper_class:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
        return scraper_class(config)
    
    @classmethod
    def register_scraper(cls, name: str, scraper_class):
        """Register new scraper type"""
        cls._scrapers[name] = scraper_class