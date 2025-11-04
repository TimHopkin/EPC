import requests
import pandas as pd
from typing import Dict, List, Optional
from tqdm import tqdm
import logging

from .auth import EPCAuth
from .pagination import SearchAfterPaginator
from config.settings import Config

logger = logging.getLogger(__name__)

class EPCClient:
    def __init__(self):
        self.auth = EPCAuth()
        self.session = self._create_session()
        self.paginator = SearchAfterPaginator(self.session, Config.EPC_API_BASE_URL)
        
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(self.auth.get_auth_headers())
        return session
    
    def test_connection(self) -> bool:
        return self.auth.test_connection()
    
    def search_domestic(self, filters: Dict) -> pd.DataFrame:
        return self._search('domestic/search', filters)
    
    def search_non_domestic(self, filters: Dict) -> pd.DataFrame:
        return self._search('non-domestic/search', filters)
    
    def search_by_postcode(self, postcode: str, property_type: str = 'domestic') -> pd.DataFrame:
        filters = {'postcode': postcode}
        endpoint = f'{property_type}/search'
        return self._search(endpoint, filters)
    
    def search_by_local_authority(self, local_authority: str, 
                                 property_type: str = 'domestic',
                                 additional_filters: Optional[Dict] = None) -> pd.DataFrame:
        filters = {'local-authority': local_authority}
        
        if additional_filters:
            filters.update(additional_filters)
        
        endpoint = f'{property_type}/search'
        return self._search(endpoint, filters)
    
    def search_by_uprn(self, uprn: str, property_type: str = 'domestic') -> pd.DataFrame:
        filters = {'uprn': uprn}
        endpoint = f'{property_type}/search'
        return self._search(endpoint, filters)
    
    def search_agricultural_buildings(self, local_authority: Optional[str] = None, 
                                    postcode: Optional[str] = None) -> pd.DataFrame:
        filters = {}
        
        if local_authority:
            filters['local-authority'] = local_authority
        if postcode:
            filters['postcode'] = postcode
            
        filters.update({
            'property-type': 'Other',
            'built-form': 'Detached'
        })
        
        return self.search_non_domestic(filters)
    
    def _search(self, endpoint: str, params: Dict) -> pd.DataFrame:
        logger.info(f"Starting search: {endpoint} with params: {params}")
        
        all_data = []
        total_records = 0
        
        pages = list(self.paginator.paginate(endpoint, params))
        
        if not pages:
            logger.warning("No data returned from API")
            return pd.DataFrame()
        
        progress_bar = tqdm(pages, desc="Processing pages", unit="page")
        
        for page_data in progress_bar:
            data = page_data['data']
            all_data.extend(data)
            total_records = page_data['total_retrieved']
            
            progress_bar.set_description(f"Processing pages ({total_records} records)")
        
        if all_data:
            df = pd.DataFrame(all_data)
            logger.info(f"Search complete: {len(df)} records retrieved")
            return df
        else:
            logger.info("No records found matching search criteria")
            return pd.DataFrame()
    
    def get_certificate_by_id(self, certificate_id: str, 
                             property_type: str = 'domestic') -> Optional[Dict]:
        endpoint = f'{property_type}/certificate/{certificate_id}'
        url = f"{Config.EPC_API_BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get certificate {certificate_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting certificate {certificate_id}: {str(e)}")
            return None