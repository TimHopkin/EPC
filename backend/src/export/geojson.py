import pandas as pd
import json
from typing import Dict, List, Optional
from pathlib import Path
import logging

from src.data.geocoder import AddressGeocoder
from config.settings import Config

logger = logging.getLogger(__name__)

class GeoJSONExporter:
    def __init__(self, export_path: Optional[str] = None):
        self.export_path = Path(export_path or Config.DEFAULT_EXPORT_PATH)
        self.export_path.mkdir(parents=True, exist_ok=True)
        self.geocoder = AddressGeocoder()
    
    def export(self, data: pd.DataFrame, filename: str, 
               include_properties: Optional[List[str]] = None) -> str:
        if data.empty:
            logger.warning("No data to export")
            return ""
        
        geocoded_data = self._ensure_coordinates(data)
        
        geojson = self._create_geojson_structure(geocoded_data, include_properties)
        
        filepath = self.export_path / f"{filename}.geojson"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(geojson['features'])} features to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export GeoJSON: {str(e)}")
            return ""
    
    def _ensure_coordinates(self, data: pd.DataFrame) -> pd.DataFrame:
        if 'latitude' not in data.columns or 'longitude' not in data.columns:
            logger.info("Geocoding addresses for GeoJSON export...")
            data = self.geocoder.geocode_dataframe(data)
        
        valid_coords = data.dropna(subset=['latitude', 'longitude'])
        
        if len(valid_coords) < len(data):
            missing = len(data) - len(valid_coords)
            logger.warning(f"{missing} records missing coordinates, excluding from GeoJSON")
        
        return valid_coords
    
    def _create_geojson_structure(self, data: pd.DataFrame, 
                                 include_properties: Optional[List[str]] = None) -> Dict:
        features = []
        
        for _, row in data.iterrows():
            try:
                lat = float(row['latitude'])
                lng = float(row['longitude'])
                
                properties = self._extract_properties(row, include_properties)
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "properties": properties
                }
                
                features.append(feature)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid coordinates in row, skipping: {str(e)}")
                continue
        
        geojson = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": Config.GEOJSON_CRS
                }
            },
            "features": features
        }
        
        return geojson
    
    def _extract_properties(self, row: pd.Series, 
                          include_properties: Optional[List[str]] = None) -> Dict:
        if include_properties:
            properties = {}
            for prop in include_properties:
                if prop in row.index and pd.notna(row[prop]):
                    properties[prop] = self._serialize_value(row[prop])
        else:
            properties = {}
            for col, value in row.items():
                if col not in ['latitude', 'longitude'] and pd.notna(value):
                    properties[col] = self._serialize_value(value)
        
        properties['full_address'] = self._create_full_address(row)
        
        return properties
    
    def _serialize_value(self, value):
        if pd.isna(value):
            return None
        elif isinstance(value, (int, float, str, bool)):
            return value
        else:
            return str(value)
    
    def _create_full_address(self, row: pd.Series) -> str:
        address_parts = []
        
        for col in ['address1', 'address2', 'address3']:
            if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                address_parts.append(str(row[col]).strip())
        
        if 'postcode' in row.index and pd.notna(row['postcode']):
            address_parts.append(str(row['postcode']).strip())
        
        return ", ".join(address_parts)
    
    def export_for_landapp(self, data: pd.DataFrame, filename: str) -> str:
        landapp_properties = [
            'lmk-key',
            'address1',
            'address2', 
            'postcode',
            'local-authority',
            'current-energy-rating',
            'potential-energy-rating',
            'current-energy-efficiency',
            'potential-energy-efficiency',
            'co2-emissions-current',
            'co2-emissions-potential',
            'total-floor-area',
            'property-type',
            'built-form',
            'inspection-date',
            'lodgement-date',
            'uprn'
        ]
        
        return self.export(data, filename, landapp_properties)
    
    def export_agricultural_geojson(self, data: pd.DataFrame, 
                                  area_name: str = "area") -> str:
        agricultural_properties = [
            'address1',
            'address2',
            'postcode', 
            'local-authority',
            'current-energy-rating',
            'potential-energy-rating',
            'total-floor-area',
            'property-type',
            'built-form',
            'main-fuel',
            'inspection-date',
            'co2-emissions-current',
            'lighting-cost-current',
            'heating-cost-current'
        ]
        
        filename = f"agricultural_buildings_{area_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        
        return self.export(data, filename, agricultural_properties)
    
    def create_summary_geojson(self, data: pd.DataFrame, 
                             group_by: str = 'postcode') -> Dict:
        if data.empty:
            return {"type": "FeatureCollection", "features": []}
        
        geocoded_data = self._ensure_coordinates(data)
        
        summary = geocoded_data.groupby(group_by).agg({
            'latitude': 'mean',
            'longitude': 'mean',
            'current-energy-rating': lambda x: x.value_counts().to_dict(),
            'lmk-key': 'count',
            'current-energy-efficiency': 'mean'
        }).reset_index()
        
        features = []
        
        for _, row in summary.iterrows():
            properties = {
                group_by: row[group_by],
                'property_count': int(row['lmk-key']),
                'avg_energy_efficiency': float(row['current-energy-efficiency']),
                'energy_rating_distribution': row['current-energy-rating']
            }
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['longitude']), float(row['latitude'])]
                },
                "properties": properties
            }
            
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": Config.GEOJSON_CRS
                }
            },
            "features": features
        }