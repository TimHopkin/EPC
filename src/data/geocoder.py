import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import logging

from config.settings import Config

logger = logging.getLogger(__name__)

class AddressGeocoder:
    def __init__(self, use_os_places: bool = True):
        self.use_os_places = use_os_places and bool(Config.OS_PLACES_API_KEY)
        self.os_api_key = Config.OS_PLACES_API_KEY
        
        if not self.use_os_places:
            self.nominatim = Nominatim(user_agent="epc-tool-geocoder")
            logger.info("Using Nominatim geocoder (OS Places API key not available)")
        else:
            logger.info("Using OS Places API for geocoding")
    
    def geocode_address(self, address: str, postcode: str = None) -> Optional[Tuple[float, float]]:
        if self.use_os_places:
            return self._geocode_with_os_places(address, postcode)
        else:
            return self._geocode_with_nominatim(address, postcode)
    
    def _geocode_with_os_places(self, address: str, postcode: str = None) -> Optional[Tuple[float, float]]:
        try:
            base_url = "https://api.os.uk/search/places/v1/postcode"
            
            search_text = postcode if postcode else address
            
            params = {
                'postcode': search_text,
                'key': self.os_api_key,
                'output_srs': 'WGS84'
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results'):
                    result = data['results'][0]
                    if 'DPA' in result:
                        lat = result['DPA']['LAT']
                        lng = result['DPA']['LNG']
                        return (float(lat), float(lng))
                    elif 'LPI' in result:
                        lat = result['LPI']['LAT']
                        lng = result['LPI']['LNG']
                        return (float(lat), float(lng))
            
            logger.warning(f"OS Places API: No results for {search_text}")
            return None
            
        except Exception as e:
            logger.error(f"OS Places geocoding failed for {address}: {str(e)}")
            return self._geocode_with_nominatim(address, postcode)
    
    def _geocode_with_nominatim(self, address: str, postcode: str = None) -> Optional[Tuple[float, float]]:
        try:
            search_address = f"{address}, {postcode}, UK" if postcode else f"{address}, UK"
            
            location = self.nominatim.geocode(search_address, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
            
            if postcode and address != postcode:
                location = self.nominatim.geocode(f"{postcode}, UK", timeout=10)
                if location:
                    return (location.latitude, location.longitude)
            
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Nominatim geocoding failed for {address}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error for {address}: {str(e)}")
            return None
    
    def geocode_dataframe(self, df: pd.DataFrame, 
                         address_col: str = 'address1',
                         postcode_col: str = 'postcode') -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        df['latitude'] = None
        df['longitude'] = None
        
        total_rows = len(df)
        geocoded_count = 0
        
        logger.info(f"Starting geocoding for {total_rows} addresses")
        
        for idx, row in df.iterrows():
            address = str(row.get(address_col, ''))
            postcode = str(row.get(postcode_col, ''))
            
            if not address and not postcode:
                continue
            
            coords = self.geocode_address(address, postcode)
            
            if coords:
                df.at[idx, 'latitude'] = coords[0]
                df.at[idx, 'longitude'] = coords[1]
                geocoded_count += 1
            
            if (idx + 1) % 10 == 0:
                logger.info(f"Geocoded {idx + 1}/{total_rows} addresses "
                           f"({geocoded_count} successful)")
            
            time.sleep(0.1)
        
        success_rate = (geocoded_count / total_rows) * 100 if total_rows > 0 else 0
        logger.info(f"Geocoding complete: {geocoded_count}/{total_rows} "
                   f"addresses geocoded ({success_rate:.1f}% success rate)")
        
        return df
    
    def create_address_string(self, row: pd.Series) -> str:
        address_parts = []
        
        for col in ['address1', 'address2', 'address3']:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                address_parts.append(str(row[col]).strip())
        
        if 'postcode' in row and pd.notna(row['postcode']):
            address_parts.append(str(row['postcode']).strip())
        
        return ", ".join(address_parts)
    
    def batch_geocode(self, addresses: List[str], 
                     batch_size: int = 50) -> List[Optional[Tuple[float, float]]]:
        results = []
        
        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]
            batch_results = []
            
            for address in batch:
                coords = self.geocode_address(address)
                batch_results.append(coords)
                time.sleep(0.1)
            
            results.extend(batch_results)
            logger.info(f"Geocoded batch {i//batch_size + 1}, "
                       f"{len([r for r in batch_results if r])} successful")
        
        return results