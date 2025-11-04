import pandas as pd
from typing import List, Optional
from pathlib import Path
import logging

from config.settings import Config

logger = logging.getLogger(__name__)

class CSVExporter:
    def __init__(self, export_path: Optional[str] = None):
        self.export_path = Path(export_path or Config.DEFAULT_EXPORT_PATH)
        self.export_path.mkdir(parents=True, exist_ok=True)
    
    def export(self, data: pd.DataFrame, filename: str, 
               columns: Optional[List[str]] = None) -> str:
        if data.empty:
            logger.warning("No data to export")
            return ""
        
        if columns:
            available_columns = [col for col in columns if col in data.columns]
            if available_columns:
                data = data[available_columns]
            else:
                logger.warning("None of the specified columns found in data")
        
        filepath = self.export_path / f"{filename}.csv"
        
        try:
            data.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported {len(data)} records to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            return ""
    
    def export_agricultural_summary(self, data: pd.DataFrame, 
                                  area_name: str = "area") -> str:
        if data.empty:
            return ""
        
        summary_columns = [
            'address1', 'address2', 'postcode', 'local-authority',
            'current-energy-rating', 'potential-energy-rating',
            'current-energy-efficiency', 'potential-energy-efficiency',
            'total-floor-area', 'property-type', 'built-form',
            'inspection-date', 'lodgement-date'
        ]
        
        filename = f"agricultural_buildings_{area_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        
        return self.export(data, filename, summary_columns)
    
    def export_supply_chain_report(self, data: pd.DataFrame, 
                                  supplier_name: str = "supplier") -> str:
        if data.empty:
            return ""
        
        supply_chain_columns = [
            'uprn', 'address1', 'address2', 'postcode',
            'current-energy-rating', 'current-energy-efficiency',
            'co2-emissions-current', 'lighting-cost-current',
            'heating-cost-current', 'hot-water-cost-current',
            'total-floor-area', 'property-type',
            'main-fuel', 'main-heating-controls',
            'inspection-date'
        ]
        
        filename = f"supply_chain_{supplier_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        
        return self.export(data, filename, supply_chain_columns)
    
    def export_energy_trends(self, data: pd.DataFrame, 
                           area_name: str = "area") -> str:
        if data.empty:
            return ""
        
        try:
            data['inspection_year'] = pd.to_datetime(data['inspection-date']).dt.year
            
            trends = data.groupby(['inspection_year', 'current-energy-rating']).size().unstack(fill_value=0)
            trends = trends.reset_index()
            
            filename = f"energy_trends_{area_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            filepath = self.export_path / f"{filename}.csv"
            
            trends.to_csv(filepath, index=False)
            logger.info(f"Exported energy trends to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export trends: {str(e)}")
            return ""
    
    def export_filtered(self, data: pd.DataFrame, filters: dict, 
                       filename_prefix: str = "filtered_epc") -> str:
        if data.empty:
            return ""
        
        filtered_data = data.copy()
        
        for column, value in filters.items():
            if column in filtered_data.columns:
                if isinstance(value, list):
                    filtered_data = filtered_data[filtered_data[column].isin(value)]
                else:
                    filtered_data = filtered_data[filtered_data[column] == value]
        
        if filtered_data.empty:
            logger.warning("No data matches the specified filters")
            return ""
        
        filter_desc = "_".join([f"{k}_{str(v).replace(' ', '')}" 
                               for k, v in filters.items()])
        filename = f"{filename_prefix}_{filter_desc}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        
        return self.export(filtered_data, filename)