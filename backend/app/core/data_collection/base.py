from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel
import aiohttp

class Document(BaseModel):
    """Data class for collected documents"""
    id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert Document to dictionary for easier serialization"""
        return {
            'id': self.id,
            'content': self.content,
            'metadata': {
                'url': self.metadata.get('url'),
                'title': self.metadata.get('title'),
                'author': self.metadata.get('author'),
                'published_date': self.metadata.get('published_date'),

            },
            'source': self.source,
            'timestamp': self.timestamp.isoformat()
        }


class BaseCrawler(ABC):
    """Abstract base class for all crawlers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def crawl(self, topic: str, limit: int = 100) -> List[Document]:
        """Crawl data based on topic"""
        pass

    
class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.documents: List[Document] = []
    
    @abstractmethod
    async def scrape(self, topic: str, num_workers: int = 4, save: bool = True)->None:
        """Scrape data based on topic"""
        pass

    @staticmethod
    @abstractmethod
    async def validate(document: Document) -> bool:
        """Validate document quality"""
        pass
    
    async def save_documents(self, path: str) -> None:
        import json
        # This creates a JSON string directly with correct date formatting
        # Note: We manually wrap it in a list format here
        json_data = "[" + ",".join(doc.model_dump_json() for doc in self.documents) + "]"
        
        with open(path, 'w') as f:
            f.write(json_data)