import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    EPC_API_EMAIL = os.getenv('EPC_API_EMAIL')
    EPC_API_KEY = os.getenv('EPC_API_KEY')
    # Legacy support for old variable names
    EPC_API_USERNAME = os.getenv('EPC_API_USERNAME')
    EPC_API_PASSWORD = os.getenv('EPC_API_PASSWORD')
    EPC_API_BASE_URL = os.getenv('EPC_API_BASE_URL', 'https://epc.opendatacommunities.org/api/v1')
    
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/epc_cache.db')
    
    OS_PLACES_API_KEY = os.getenv('OS_PLACES_API_KEY')
    
    DEFAULT_EXPORT_PATH = os.getenv('DEFAULT_EXPORT_PATH', 'exports/')
    GEOJSON_CRS = os.getenv('GEOJSON_CRS', 'EPSG:4326')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    REQUEST_TIMEOUT = 30
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1
    
    PAGE_SIZE = 5000