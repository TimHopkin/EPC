import requests
import time
from typing import Dict, List, Optional, Generator
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class SearchAfterPaginator:
    def __init__(self, session: requests.Session, base_url: str):
        self.session = session
        self.base_url = base_url
        
    def paginate(self, endpoint: str, params: Dict, 
                 search_after_key: str = 'search-after') -> Generator[Dict, None, None]:
        search_after = None
        page_count = 0
        total_records = 0
        
        while True:
            page_params = params.copy()
            
            if search_after:
                page_params[search_after_key] = search_after
            
            page_params['size'] = Config.PAGE_SIZE
            
            try:
                response = self._make_request(endpoint, page_params)
                
                if not response:
                    logger.warning(f"No response received for page {page_count + 1}")
                    break
                    
                # Handle both formats: 'data' array or 'column-names'/'rows' format
                if 'data' in response:
                    data = response.get('data', [])
                elif 'rows' in response and 'column-names' in response:
                    # Convert column-names/rows format to data array
                    columns = response['column-names']
                    rows = response['rows']
                    data = [dict(zip(columns, row)) for row in rows]
                else:
                    data = []
                if not data:
                    logger.info(f"No more data available after {page_count} pages")
                    break
                
                page_count += 1
                total_records += len(data)
                
                logger.info(f"Page {page_count}: Retrieved {len(data)} records "
                           f"(total: {total_records})")
                
                yield {
                    'data': data,
                    'page': page_count,
                    'page_size': len(data),
                    'total_retrieved': total_records
                }
                
                search_after = response.get('next-search-after')
                if not search_after:
                    logger.info(f"Pagination complete: {total_records} total records")
                    break
                    
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error on page {page_count + 1}: {str(e)}")
                break
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(Config.RETRY_ATTEMPTS):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=Config.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * Config.RETRY_DELAY
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    return None
                    
            except requests.RequestException as e:
                if attempt < Config.RETRY_ATTEMPTS - 1:
                    wait_time = (attempt + 1) * Config.RETRY_DELAY
                    logger.warning(f"Request failed, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {Config.RETRY_ATTEMPTS} attempts: {str(e)}")
                    return None
        
        return None