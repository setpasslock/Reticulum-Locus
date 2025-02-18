import ipaddress
from typing import List, Dict, Optional, Set, Tuple

class IPRangeStorage:
    def __init__(self):
        self.ranges: Dict = {}
        self.current_query_id: int = 0
        self.selections: Dict = {}
    
    def add_range(self, query_type: str, query_value: str, results: List[Dict]) -> str:
        self.current_query_id += 1
        query_key = f"{query_type}_{self.current_query_id}"
        
        ip_ranges = []
        
        for row in results:
            start_ip = ipaddress.IPv4Address(row['ip_from'])
            end_ip = ipaddress.IPv4Address(row['ip_to'])
            
            ip_ranges.append({
                'start': start_ip,
                'end': end_ip,
                'location': {
                    'city': row['city_name'],
                    'region': row['region_name'],
                    'country': row['country_name'],
                    'country_code': row['country_code']
                }
            })
        
        self.ranges[query_key] = {
            'query_type': query_type,
            'query_value': query_value,
            'ip_ranges': ip_ranges,
        }
        
        return query_key
    
    def get_ranges(self, query_key: Optional[str] = None) -> Dict:
        if query_key:
            return self.ranges.get(query_key)
        return self.ranges
    
    def get_ip_list(self, query_key: str) -> List[str]:
        if query_key not in self.ranges:
            return []
        
        ips = []
        for ip_range in self.ranges[query_key]['ip_ranges']:
            start_ip = ip_range['start']
            end_ip = ip_range['end']
            ips.extend([str(ipaddress.IPv4Address(ip)) for ip in range(int(start_ip), int(end_ip) + 1)])
        return ips
    
    def get_range_list(self, query_key: str) -> List[Tuple[str, str]]:
        if query_key not in self.ranges:
            return []
        
        return [(str(r['start']), str(r['end'])) for r in self.ranges[query_key]['ip_ranges']]
    
    def create_selection(self, query_id: str, selection_str: str) -> Optional[str]:
        if query_id not in self.ranges:
            return None
        
        total_ranges = len(self.ranges[query_id]['ip_ranges'])
        selected_indices: Set[int] = set()
        
        try:
            parts = selection_str.split(',')
            for part in parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    if start < 1 or end > total_ranges:
                        raise ValueError(f"Invalid range: {start}-{end}")
                    selected_indices.update(range(start-1, end))
                else:
                    idx = int(part)
                    if idx < 1 or idx > total_ranges:
                        raise ValueError(f"Invalid index: {idx}")
                    selected_indices.add(idx-1)
            
            selected_indices = sorted(list(selected_indices))
            
            selection_id = f"{query_id}_sel_{len(self.selections)+1}"
            
            selected_ranges = [self.ranges[query_id]['ip_ranges'][i] for i in selected_indices]
            
            self.selections[selection_id] = {
                'query_id': query_id,
                'indices': selected_indices,
                'ip_ranges': selected_ranges,
                'selection_str': selection_str
            }
            
            return selection_id
            
        except (ValueError, IndexError) as e:
            return None
    
    def get_selection(self, selection_id: str) -> Optional[Dict]:
        return self.selections.get(selection_id)
    
    def get_selection_ip_list(self, selection_id: str) -> List[str]:
        selection = self.selections.get(selection_id)
        if not selection:
            return []
        
        ips = []
        for ip_range in selection['ip_ranges']:
            start_ip = ip_range['start']
            end_ip = ip_range['end']
            ips.extend([str(ipaddress.IPv4Address(ip)) for ip in range(int(start_ip), int(end_ip) + 1)])
        return ips
    
    def get_selection_range_list(self, selection_id: str) -> List[Tuple[str, str]]:
        selection = self.selections.get(selection_id)
        if not selection:
            return []
        
        return [(str(r['start']), str(r['end'])) for r in selection['ip_ranges']]