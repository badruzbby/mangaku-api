import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mangaku-api-secret-key-2025'
    DEBUG = False
    TESTING = False
    
    # Rate Limiting settings
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    RATELIMIT_DEFAULT = "100 per hour, 20 per minute"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Caching settings
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = "mangaku_api:"
    
    # Performance settings
    JSONIFY_PRETTYPRINT_REGULAR = False  # Disable pretty printing for performance
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
    # Scraper settings - Increased timeouts to prevent timeout errors
    REQUEST_TIMEOUT = 120  # Increased from 30 to 120 seconds
    MAX_RETRIES = 5  # Increased from 3 to 5
    SCRAPER_DELAY = 0.5  # Reduced delay between requests
    CONNECTION_POOL_SIZE = 20  # Connection pool size
    CONNECTION_POOL_MAXSIZE = 50  # Max connections per pool
    
    # Pagination settings
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    CACHE_DEFAULT_TIMEOUT = 60  # Shorter cache for development
    RATELIMIT_DEFAULT = "1000 per hour, 100 per minute"  # More lenient for development
    REQUEST_TIMEOUT = 180  # Even longer timeout for development/testing

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes cache for production
    RATELIMIT_DEFAULT = "100 per hour, 20 per minute"  # Strict rate limiting
    REQUEST_TIMEOUT = 150  # Longer timeout for production stability
    MAX_RETRIES = 3  # Conservative retries for production
    
    # Production optimizations
    JSONIFY_PRETTYPRINT_REGULAR = False
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    CACHE_TYPE = "SimpleCache"  # Use simple cache for testing
    RATELIMIT_ENABLED = False  # Disable rate limiting for tests
    REQUEST_TIMEOUT = 60  # Shorter timeout for tests

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 