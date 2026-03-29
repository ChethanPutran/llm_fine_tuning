from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Document:
    """Data class for collected documents"""
    id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    timestamp: datetime = datetime.now()
    
class BaseCrawler(ABC):
    """Abstract base class for all crawlers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.documents: List[Document] = []
    
    @abstractmethod
    async def crawl(self, topic: str, limit: int = 100) -> List[Document]:
        """Crawl data based on topic"""
        pass
    
    @abstractmethod
    async def validate(self, document: Document) -> bool:
        """Validate document quality"""
        pass
    
    def save_documents(self, path: str) -> None:
        """Save collected documents"""
        import json
        with open(path, 'w') as f:
            json.dump([doc.__dict__ for doc in self.documents], f)