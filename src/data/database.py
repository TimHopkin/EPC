import sqlite3
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from config.settings import Config

logger = logging.getLogger(__name__)

class EPCDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.ensure_database_exists()
        self._create_tables()
    
    def ensure_database_exists(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS epc_certificates (
                    certificate_id TEXT PRIMARY KEY,
                    property_type TEXT NOT NULL,
                    data JSON NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_cache (
                    search_hash TEXT PRIMARY KEY,
                    search_params JSON NOT NULL,
                    result_count INTEGER,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cached_at 
                ON epc_certificates(cached_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_property_type 
                ON epc_certificates(property_type)
            ''')
            
            conn.commit()
    
    def store_certificates(self, data: pd.DataFrame, property_type: str):
        if data.empty:
            logger.warning("No data to store")
            return
        
        records_stored = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for _, row in data.iterrows():
                try:
                    certificate_id = row.get('lmk-key') or row.get('building-reference-number')
                    
                    if not certificate_id:
                        continue
                    
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO epc_certificates 
                        (certificate_id, property_type, data, cached_at, last_accessed)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (
                        certificate_id,
                        property_type,
                        json.dumps(row.to_dict())
                    ))
                    
                    records_stored += 1
                    
                except Exception as e:
                    logger.error(f"Error storing certificate: {str(e)}")
                    continue
            
            conn.commit()
        
        logger.info(f"Stored {records_stored} certificates in cache")
    
    def get_certificates(self, filters: Dict, property_type: str, 
                        max_age_hours: int = 24) -> pd.DataFrame:
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT data FROM epc_certificates 
                WHERE property_type = ? AND cached_at > ?
            '''
            params = [property_type, cutoff_time.isoformat()]
            
            if 'postcode' in filters:
                query += ' AND json_extract(data, "$.postcode") = ?'
                params.append(filters['postcode'])
            
            if 'local-authority' in filters:
                query += ' AND json_extract(data, "$.local-authority") = ?'
                params.append(filters['local-authority'])
            
            if 'uprn' in filters:
                query += ' AND json_extract(data, "$.uprn") = ?'
                params.append(filters['uprn'])
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            
            if results:
                data = []
                for row in results:
                    try:
                        data.append(json.loads(row[0]))
                    except json.JSONDecodeError:
                        continue
                
                if data:
                    logger.info(f"Retrieved {len(data)} certificates from cache")
                    return pd.DataFrame(data)
        
        return pd.DataFrame()
    
    def get_certificate_by_id(self, certificate_id: str, 
                             max_age_hours: int = 24) -> Optional[Dict]:
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data FROM epc_certificates 
                WHERE certificate_id = ? AND cached_at > ?
            ''', (certificate_id, cutoff_time.isoformat()))
            
            result = cursor.fetchone()
            
            if result:
                cursor.execute('''
                    UPDATE epc_certificates 
                    SET last_accessed = CURRENT_TIMESTAMP 
                    WHERE certificate_id = ?
                ''', (certificate_id,))
                conn.commit()
                
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return None
        
        return None
    
    def cleanup_old_data(self, max_age_days: int = 30):
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM epc_certificates 
                WHERE last_accessed < ?
            ''', (cutoff_time.isoformat(),))
            
            deleted_count = cursor.rowcount
            
            cursor.execute('''
                DELETE FROM search_cache 
                WHERE last_accessed < ?
            ''', (cutoff_time.isoformat(),))
            
            deleted_searches = cursor.rowcount
            
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} certificates and {deleted_searches} searches")
    
    def get_cache_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM epc_certificates')
            total_certificates = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT property_type, COUNT(*) 
                FROM epc_certificates 
                GROUP BY property_type
            ''')
            by_type = dict(cursor.fetchall())
            
            cursor.execute('''
                SELECT COUNT(*) FROM epc_certificates 
                WHERE cached_at > datetime('now', '-24 hours')
            ''')
            recent_certificates = cursor.fetchone()[0]
            
            return {
                'total_certificates': total_certificates,
                'by_property_type': by_type,
                'recent_certificates': recent_certificates,
                'database_path': self.db_path
            }