import sqlite3
import requests
import zipfile
import os
import hashlib
from io import BytesIO
import csv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IP2LocationUpdater:
    def __init__(self, db_path="ip2location.db"):
        self.db_path = db_path
        
    def _calculate_file_hash(self, file_content):
        return hashlib.sha256(file_content).hexdigest()
        
    def _download_database(self, token):
        url = f"https://www.ip2location.com/download/?token={token}&file=DB5LITECSV"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Failed to download database: {e}")
            raise
            
    def _extract_csv(self, zip_content):
        zip_file = BytesIO(zip_content)
        with zipfile.ZipFile(zip_file) as z:
            csv_filename = next(name for name in z.namelist() if name.endswith('.CSV'))
            return z.read(csv_filename)
            
    def _create_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ip2location (
                    ip_from INTEGER,
                    ip_to INTEGER,
                    country_code TEXT,
                    country_name TEXT,
                    region_name TEXT,
                    city_name TEXT,
                    latitude REAL,
                    longitude REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
    def _import_csv_to_db(self, csv_content):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM ip2location")
            
            csv_file = BytesIO(csv_content)
            csv_reader = csv.reader(csv_file.getvalue().decode('utf-8').splitlines())
            
            conn.executemany(
                "INSERT INTO ip2location VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tuple(row) for row in csv_reader)
            )
            
    def update_database(self, token):
        logger.info("Downloading IP2Location database...")
        zip_content = self._download_database(token)
        
        file_hash = self._calculate_file_hash(zip_content)
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                stored_hash = conn.execute(
                    "SELECT value FROM metadata WHERE key = 'file_hash'"
                ).fetchone()
                
                if stored_hash and stored_hash[0] == file_hash:
                    count = conn.execute("SELECT COUNT(*) FROM ip2location").fetchone()[0]
                    if count > 0:
                        logger.info("Database is already up to date")
                        return False
            except sqlite3.OperationalError:
                pass
        
        logger.info("Extracting CSV file...")
        csv_content = self._extract_csv(zip_content)
        
        logger.info("Creating database...")
        self._create_database()
        
        logger.info("Importing data...")
        self._import_csv_to_db(csv_content)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                        ('file_hash', file_hash))
        
        logger.info("Database update completed")
        return True
        
    def ensure_database_exists(self, token):
        need_update = False
        
        if not os.path.exists(self.db_path):
            need_update = True
        else:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    try:
                        count = conn.execute("SELECT COUNT(*) FROM ip2location").fetchone()[0]
                        if count == 0:
                            need_update = True
                            
                        metadata_count = conn.execute("SELECT COUNT(*) FROM metadata").fetchone()[0]
                        if metadata_count == 0:
                            need_update = True
                    except sqlite3.OperationalError:
                        need_update = True
            except sqlite3.DatabaseError:
                need_update = True
                os.remove(self.db_path)
        
        if need_update:
            return self.update_database(token)
            
        return True