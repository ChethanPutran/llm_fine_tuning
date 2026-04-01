
from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Optional

class BaseConfig(BaseModel):
    """Base configuration for scrapers"""
    num_workers: int = 4
    additional_params: Optional[Dict[str, Any]] = None


class WebScraperConfig(BaseModel):
    """Scraper configuration model"""
    rate_limit: float = Field(default=1.0, ge=0.1, le=10.0, description="Rate limit for scraping (requests per second)")
    timeout: int = Field(default=10, ge=1, le=60, description="Timeout for scraping requests (seconds)")
    search_engine: Optional[str] = Field(default=None, description="Search engine to use for web scraping (google, bing, duckduckgo)")
    platform: Optional[str] = Field(default=None, description="Social media platform to scrape (twitter, reddit)")
    api_endpoint: Optional[str] = Field(default=None, description="API endpoint for data collection")
    api_key: Optional[str] = Field(default=None, description="API key for data collection")
    file_path: Optional[str] = Field(default=None, description="File path for data collection from files")
    file_type: Optional[str] = Field(default=None, description="File type for data collection from files (csv, json)")

class BookScraperConfig(BaseModel):
    """Book scraper configuration model"""
    rate_limit: float = Field(default=1.0, ge=0.1, le=10.0, description="Rate limit for scraping (requests per second)")
    timeout: int = Field(default=10, ge=1, le=60, description="Timeout for scraping requests (seconds)")
    source: Optional[str] = Field(default=None, description="Source to scrape books from (goodreads, openlibrary)")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for book scraping")


class DataCollectionConfig(BaseModel):
    """Data collection configuration model with built-in validation"""
    limit: int = Field(default=100, ge=1, le=10000)
    source: str = Field(default="web", description="Data source (web, api, database)")
    topic: str = Field(default="", description="Topic or query")
    additional_params: Dict[str, Any] = Field(default_factory=dict)
    scraper_config: BaseConfig = Field(default=BaseConfig(), description="Configuration for the scraper to use in data collection")

    @model_validator(mode='after')
    def validate_logic(self) -> 'DataCollectionConfig':
        """
        Logic-based validation that runs after fields are assigned.
        Self refers to the instance of the config.
        """
        # Scraper Config Check for Web
        if self.source == 'web':
            if not self.scraper_config or not isinstance(self.scraper_config, WebScraperConfig):
                raise ValueError("Web source requires a valid WebScraperConfig")
        elif self.source == 'books':
            if not self.scraper_config or not isinstance(self.scraper_config, BookScraperConfig):
                raise ValueError("Books source requires a valid BookScraperConfig")
        return self