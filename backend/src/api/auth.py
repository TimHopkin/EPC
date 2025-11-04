import base64
import requests
from typing import Optional
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class EPCAuth:
    def __init__(self):
        # Try new format first (email:api_key)
        self.email = Config.EPC_API_EMAIL
        self.api_key = Config.EPC_API_KEY
        
        # Fallback to legacy format if new format not available
        if not self.email and Config.EPC_API_USERNAME:
            self.email = Config.EPC_API_USERNAME
        if not self.api_key and Config.EPC_API_PASSWORD:
            self.api_key = Config.EPC_API_PASSWORD
            
        self.base_url = Config.EPC_API_BASE_URL
        self.token = None
        
    def _validate_credentials(self) -> bool:
        if not self.email or not self.api_key:
            raise ValueError("EPC_API_EMAIL and EPC_API_KEY must be set in environment variables")
        return True
    
    def _generate_basic_auth_header(self) -> str:
        credentials = f"{self.email}:{self.api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    def get_auth_headers(self) -> dict:
        self._validate_credentials()
        return {
            'Authorization': self._generate_basic_auth_header(),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> bool:
        try:
            headers = self.get_auth_headers()
            response = requests.get(
                f"{self.base_url}/domestic/search",
                headers=headers,
                params={'postcode': 'SW1A 0AA', 'size': 1},
                timeout=Config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                logger.info("EPC API authentication successful")
                return True
            else:
                logger.error(f"EPC API authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False