import sqlite3
import ipaddress

class IP2LocationQuery:
    def __init__(self, db_path="ip2location.db"):
        self.db_path = db_path
    
    def _int_to_ip(self, ip_int):
        return str(ipaddress.IPv4Address(ip_int))
    
    def search_by_city(self, city_name):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    ip_from, ip_to, 
                    country_code, country_name,
                    region_name, city_name,
                    latitude, longitude
                FROM ip2location
                WHERE LOWER(city_name) = LOWER(?)
                ORDER BY ip_from
            """, (city_name,))
            return cursor.fetchall()
    
    def search_by_region(self, region_name):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    ip_from, ip_to, 
                    country_code, country_name,
                    region_name, city_name,
                    latitude, longitude
                FROM ip2location
                WHERE LOWER(region_name) = LOWER(?)
                ORDER BY ip_from
            """, (region_name,))
            return cursor.fetchall()
    
    def search_by_country_name(self, country_name):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    ip_from, ip_to, 
                    country_code, country_name,
                    region_name, city_name,
                    latitude, longitude
                FROM ip2location
                WHERE LOWER(country_name) = LOWER(?)
                ORDER BY ip_from
            """, (country_name,))
            return cursor.fetchall()
    
    def search_by_country_code(self, country_code):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    ip_from, ip_to, 
                    country_code, country_name,
                    region_name, city_name,
                    latitude, longitude
                FROM ip2location
                WHERE LOWER(country_code) = LOWER(?)
                ORDER BY ip_from
            """, (country_code,))
            return cursor.fetchall()