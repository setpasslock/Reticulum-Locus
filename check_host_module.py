from scapy.all import *
import csv
from datetime import datetime
import time
from concurrent import futures
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor
import os
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

def escalate_privileges():
    if os.geteuid() != 0:
        try:
            args = ['sudo', sys.executable] + sys.argv
            logging.info("[*] Root privileges required. Authorization upgrade requested...")
            os.execvp('sudo', args)
        except Exception as e:
            logging.error(f"[-] Root privilege upgrade failed: {str(e)}")
            sys.exit(1)

MODULE_INFO = {
    'name': 'Advanced Host Discovery',
    'description': 'Multi-technique stealth host discovery scanner using Scapy ( need root - experimental)',
    'version': '1.0.0',
    'options': {
        'query_id': {
            'description': 'Query ID to scan (e.g., city_1) or "all" for all ranges',
            'required': False,
            'value': None,
            'type': 'str'
        },
        'input_file': {
            'description': 'Input file containing target IPs (one per line)',
            'required': False,
            'value': None,
            'type': 'str'
        },
        'max_level': {
            'description': 'Maximum scan level (1=Basic ICMP, 2=TCP Basic, 3=Advanced TCP)',
            'required': False,
            'value': '3',
            'type': 'int'
        },
        'timeout': {
            'description': 'Timeout for each probe in milliseconds',
            'required': False,
            'value': '2500',
            'type': 'int'
        },
        'concurrent_hosts': {
            'description': 'Number of hosts to scan concurrently',
            'required': False,
            'value': '100',
            'type': 'int'
        },
        'output_file': {
            'description': 'CSV output file (default: host_discovery_<timestamp>.csv)',
            'required': False,
            'value': None,
            'type': 'str'
        }
    }
}

@dataclass
class HostResult:
    ip: str
    status: str = 'unknown'
    discovery_time: str = ''
    
    # Level 1: ICMP Results
    icmp_echo: bool = False
    icmp_timestamp: bool = False
    icmp_info: bool = False
    icmp_mask: bool = False
    
    # Level 2: Basic TCP Results
    tcp_syn_80: bool = False
    tcp_syn_443: bool = False
    tcp_syn_0: bool = False
    
    # Level 3: Advanced TCP Results
    tcp_ack: bool = False
    tcp_null: bool = False
    tcp_fin: bool = False
    tcp_xmas: bool = False
    tcp_window: bool = False
    
    # Additional Information
    os_guess: str = ''
    window_size: int = 0
    ttl: int = 0
    mss: int = 0

class HostDiscoveryScanner:
    def __init__(self):
        self.options = MODULE_INFO['options']
        self.results: Dict[str, HostResult] = {}
        self.timeout = 2.5  # default timeout in seconds
        self.concurrent_hosts = 100
        
    def _initialize_scanner(self):
        if os.geteuid() != 0:
            escalate_privileges()
            
        # Scapy configler falan
        conf.verb = 0
        self._validate_and_set_options()
        
    def _validate_and_set_options(self):
        for option_name, option in self.options.items():
            if option['value'] is not None:
                try:
                    if option['type'] == 'int':
                        option['value'] = int(option['value'])
                except ValueError as e:
                    logging.error(f"Invalid value for {option_name}: {e}")
                    option['value'] = None
        
        if self.options['timeout']['value']:
            self.timeout = self.options['timeout']['value'] / 1000
            
        if self.options['concurrent_hosts']['value']:
            self.concurrent_hosts = self.options['concurrent_hosts']['value']
            
    def validate_options(self):
        if not self.options['query_id']['value'] and not self.options['input_file']['value']:
            return False, "Either query_id or input_file must be set"
            
        if self.options['input_file']['value'] and not os.path.exists(self.options['input_file']['value']):
            return False, f"Input file {self.options['input_file']['value']} does not exist"
            
        return True, None
        
    def icmp_scan(self, target: str) -> Dict[str, bool]:
        try:
            results = {
                'echo': False,
                'timestamp': False,
                'info': False,
                'mask': False,
                'ttl': 0
            }
            
            # Echo req - type 8
            echo_reply = sr1(
                IP(dst=target)/ICMP(type=8, code=0),
                timeout=self.timeout,
                verbose=0
            )
            
            if echo_reply and echo_reply.haslayer(ICMP):
                results['echo'] = True
                results['ttl'] = echo_reply.ttl
                
            # Timestamp req - type 13
            timestamp_reply = sr1(
                IP(dst=target)/ICMP(type=13, code=0),
                timeout=self.timeout,
                verbose=0
            )
            
            if timestamp_reply and timestamp_reply.haslayer(ICMP):
                results['timestamp'] = True
                
            # Information req - type 15
            info_reply = sr1(
                IP(dst=target)/ICMP(type=15, code=0),
                timeout=self.timeout,
                verbose=0
            )
            
            if info_reply and info_reply.haslayer(ICMP):
                results['info'] = True
                
            # Address Mask Req - type 17
            mask_reply = sr1(
                IP(dst=target)/ICMP(type=17, code=0),
                timeout=self.timeout,
                verbose=0
            )
            
            if mask_reply and mask_reply.haslayer(ICMP):
                results['mask'] = True
                
            return results
        except Exception as e:
            logging.error(f"Error in ICMP scan for {target}: {str(e)}")
            return results
        
    def tcp_syn_scan(self, target: str, ports: List[int]) -> Dict[int, Dict]:
        try:
            results = {}
            
            for port in ports:
                syn_reply = sr1(
                    IP(dst=target)/TCP(dport=port, flags="S"),
                    timeout=self.timeout,
                    verbose=0
                )
                
                if syn_reply and syn_reply.haslayer(TCP):
                    results[port] = {
                        'open': bool(syn_reply[TCP].flags & 0x12),
                        'window_size': syn_reply[TCP].window,
                        'mss': (syn_reply[TCP].options[0][1] 
                               if syn_reply[TCP].options and 
                               len(syn_reply[TCP].options) > 0 and
                               syn_reply[TCP].options[0][0] == 'MSS'
                               else 0)
                    }
                else:
                    results[port] = {'open': False, 'window_size': 0, 'mss': 0}
                    
            return results
        except Exception as e:
            logging.error(f"Error in TCP SYN scan for {target}: {str(e)}")
            return {port: {'open': False, 'window_size': 0, 'mss': 0} for port in ports}
        
    def advanced_tcp_scan(self, target: str) -> Dict[str, bool]:
        try:
            results = {
                'ack': False,
                'null': False,
                'fin': False,
                'xmas': False,
                'window': False,
                'window_size': 0
            }
            
            # ACK Scan
            ack_reply = sr1(
                IP(dst=target)/TCP(dport=80, flags="A"),
                timeout=self.timeout,
                verbose=0
            )
            
            if ack_reply and ack_reply.haslayer(TCP):
                results['ack'] = True
                results['window_size'] = ack_reply[TCP].window
                
            # NULL Scan
            null_reply = sr1(
                IP(dst=target)/TCP(dport=80, flags=""),
                timeout=self.timeout,
                verbose=0
            )
            
            if null_reply and null_reply.haslayer(TCP):
                results['null'] = True
                
            # FIN Scan
            fin_reply = sr1(
                IP(dst=target)/TCP(dport=80, flags="F"),
                timeout=self.timeout,
                verbose=0
            )
            
            if fin_reply and fin_reply.haslayer(TCP):
                results['fin'] = True
                
            # XMAS Scan
            xmas_reply = sr1(
                IP(dst=target)/TCP(dport=80, flags="FPU"),
                timeout=self.timeout,
                verbose=0
            )
            
            if xmas_reply and xmas_reply.haslayer(TCP):
                results['xmas'] = True
                
            return results
        except Exception as e:
            logging.error(f"Error in advanced TCP scan for {target}: {str(e)}")
            return results
        
    def guess_os(self, ttl: int, window_size: int, mss: int) -> str:
        os_guess = ''
        
        # TTL-based guessing
        if ttl > 0:
            if ttl <= 64:
                os_guess = 'Linux/Unix'
            elif ttl <= 128:
                os_guess = 'Windows'
            elif ttl <= 255:
                os_guess = 'Cisco/Network'
                
        # Window size kontrol
        if window_size > 0:
            if window_size in [64240, 65535]:
                os_guess = 'Linux/Unix' if not os_guess else os_guess
            elif window_size in [8192, 16384, 65535]:
                os_guess = 'Windows' if not os_guess else os_guess
                
        # MSS kontrol
        if mss > 0:
            if mss in [1460, 1440]:
                os_guess = 'Linux/Unix' if not os_guess else os_guess
            elif mss in [1380, 1400]:
                os_guess = 'Windows' if not os_guess else os_guess
                
        return os_guess
        
    def scan_host(self, target: str) -> HostResult:
        try:
            result = HostResult(ip=target)
            max_level = int(self.options['max_level']['value'])
            
            # Level 1: ICMP Scans
            icmp_results = self.icmp_scan(target)
            result.icmp_echo = icmp_results['echo']
            result.icmp_timestamp = icmp_results['timestamp']
            result.icmp_info = icmp_results['info']
            result.icmp_mask = icmp_results['mask']
            result.ttl = icmp_results['ttl']
            
            if any([result.icmp_echo, result.icmp_timestamp, 
                   result.icmp_info, result.icmp_mask]):
                result.status = 'alive'
                
            # Level 2: Basic TCP Scans
            if max_level >= 2:
                tcp_results = self.tcp_syn_scan(target, [80, 443, 0])
                
                result.tcp_syn_80 = tcp_results[80]['open']
                result.tcp_syn_443 = tcp_results[443]['open']
                result.tcp_syn_0 = tcp_results[0]['open']
                
                if any([result.tcp_syn_80, result.tcp_syn_443, result.tcp_syn_0]):
                    result.status = 'alive'
                    result.window_size = max(r['window_size'] for r in tcp_results.values())
                    result.mss = max(r['mss'] for r in tcp_results.values())
                    
            # Level 3: Advanced TCP Scans
            if max_level >= 3:
                adv_results = self.advanced_tcp_scan(target)
                
                result.tcp_ack = adv_results['ack']
                result.tcp_null = adv_results['null']
                result.tcp_fin = adv_results['fin']
                result.tcp_xmas = adv_results['xmas']
                result.tcp_window = adv_results['window_size'] > 0
                
                if any([result.tcp_ack, result.tcp_null, 
                       result.tcp_fin, result.tcp_xmas]):
                    result.status = 'alive'
                    
                if adv_results['window_size'] > result.window_size:
                    result.window_size = adv_results['window_size']
                    
            # Try to guess OS
            if result.status == 'alive':
                result.os_guess = self.guess_os(result.ttl, result.window_size, result.mss)
                
            result.discovery_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if result.status == 'unknown':
                result.status = 'dead'
                
            return result
        except Exception as e:
            logging.error(f"Error scanning host {target}: {str(e)}")
            result.status = 'error'
            return result
        
        
    def scan_hosts(self, ip_list: List[str]):
        total_ips = len(ip_list)
        completed = 0
        alive_count = 0
        last_update = time.time()
        update_interval = 1.0  

        logging.info(f"\nStarting scan of {total_ips} hosts...")
        logging.info("Status: [IP Address] [Result] [OS Guess] [Detection Method]")
        logging.info("-" * 70)

        with ThreadPoolExecutor(max_workers=self.concurrent_hosts) as executor:
            future_to_ip = {executor.submit(self.scan_host, ip): ip 
                          for ip in ip_list}
            
            for future in futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    self.results[ip] = result
                    completed += 1
                    
                    if result.status == 'alive':
                        alive_count += 1
                        detection_method = []
                        if any([result.icmp_echo, result.icmp_timestamp, result.icmp_info, result.icmp_mask]):
                            detection_method.append("ICMP")
                        if any([result.tcp_syn_80, result.tcp_syn_443, result.tcp_syn_0]):
                            detection_method.append("TCP-SYN")
                        if any([result.tcp_ack, result.tcp_null, result.tcp_fin, result.tcp_xmas]):
                            detection_method.append("TCP-Advanced")
                            
                        logging.info(f"[+] {ip:15} [ALIVE] [{result.os_guess:10}] [{','.join(detection_method)}]")

                    current_time = time.time()
                    if current_time - last_update >= update_interval:
                        progress = (completed / total_ips) * 100
                        alive_percentage = (alive_count / completed) * 100 if completed > 0 else 0
                        logging.info(f"\rProgress: {progress:.1f}% ({completed}/{total_ips}) | Alive: {alive_count} ({alive_percentage:.1f}%)")
                        last_update = current_time

                except Exception as e:
                    logging.error(f"Error scanning {ip}: {str(e)}")
                    # Add error result to maintain consistency
                    self.results[ip] = HostResult(ip=ip, status='error')
                    completed += 1
                    
        logging.info(f"\n\nScan completed: {completed}/{total_ips} hosts scanned, {alive_count} alive ({(alive_count/total_ips)*100:.1f}%)")
        logging.info("-" * 70)
                    
    def save_results(self) -> str:
        try:
            if not self.options['output_file']['value']:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'host_discovery_{timestamp}.csv'
            else:
                output_file = self.options['output_file']['value']
                
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'ip', 'status', 'discovery_time',
                    'icmp_echo', 'icmp_timestamp', 'icmp_info', 'icmp_mask',
                    'tcp_syn_80', 'tcp_syn_443', 'tcp_syn_0',
                    'tcp_ack', 'tcp_null', 'tcp_fin', 'tcp_xmas', 'tcp_window',
                    'window_size', 'ttl', 'mss', 'os_guess'
                ])
                
                for result in self.results.values():
                    writer.writerow([
                        result.ip, result.status, result.discovery_time,
                        result.icmp_echo, result.icmp_timestamp,
                        result.icmp_info, result.icmp_mask,
                        result.tcp_syn_80, result.tcp_syn_443, result.tcp_syn_0,
                        result.tcp_ack, result.tcp_null, result.tcp_fin,
                        result.tcp_xmas, result.tcp_window,
                        result.window_size, result.ttl, result.mss,
                        result.os_guess
                    ])
                    
            return output_file
        except Exception as e:
            logging.error(f"Error saving results to CSV: {str(e)}")
            raise
        
    def run(self, ip_list: Optional[List[str]] = None) -> Tuple[bool, Dict]:
        try:
            self._initialize_scanner()
            
            valid, error = self.validate_options()
            if not valid:
                return False, {"error": error}
                
            if not ip_list and self.options['input_file']['value']:
                try:
                    with open(self.options['input_file']['value'], 'r', encoding='utf-8') as f:
                        ip_list = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                except Exception as e:
                    return False, {"error": f"Error reading input file: {str(e)}"}
                    
            if not ip_list:
                return False, {"error": "No IP addresses to scan"}
                
            ip_list = list(dict.fromkeys(ip_list))
            
            current_user = os.getenv('SUDO_USER') if os.getenv('SUDO_USER') else os.getenv('USER')
            logging.info(f"[+] Tarama başlatılıyor... (Kullanıcı: {current_user})")
                
            self.scan_hosts(ip_list)
            
            try:
                output_file = self.save_results()
            except Exception as e:
                return False, {"error": f"Error saving results: {str(e)}"}
            
            alive_hosts = len([r for r in self.results.values() if r.status == 'alive'])
            dead_hosts = len([r for r in self.results.values() if r.status == 'dead'])
            error_hosts = len([r for r in self.results.values() if r.status == 'error'])
            
            detection_methods = {
                'icmp': len([r for r in self.results.values() 
                           if any([r.icmp_echo, r.icmp_timestamp, 
                                 r.icmp_info, r.icmp_mask])]),
                'basic_tcp': len([r for r in self.results.values() 
                                if any([r.tcp_syn_80, r.tcp_syn_443, r.tcp_syn_0])]),
                'advanced_tcp': len([r for r in self.results.values() 
                                   if any([r.tcp_ack, r.tcp_null, r.tcp_fin, 
                                         r.tcp_xmas, r.tcp_window])])
            }
            
            os_stats = {}
            for r in self.results.values():
                if r.os_guess:
                    os_stats[r.os_guess] = os_stats.get(r.os_guess, 0) + 1
            
            summary = {
                'total_scanned': len(self.results),
                'alive_hosts': alive_hosts,
                'dead_hosts': dead_hosts,
                'error_hosts': error_hosts,
                'detection_methods': detection_methods,
                'os_distribution': os_stats,
                'output_file': output_file
            }
            
            return True, summary
            
        except Exception as e:
            logging.error(f"Error in run(): {str(e)}")
            return False, {"error": str(e)}

def create_instance():
    scanner = HostDiscoveryScanner()
    return scanner