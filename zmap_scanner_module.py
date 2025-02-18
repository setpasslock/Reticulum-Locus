import subprocess
import tempfile
import os
from datetime import datetime
import netifaces

def get_default_interface():
    try:
        gateways = netifaces.gateways()
        default_gateway = gateways.get('default', {}).get(netifaces.AF_INET)
        if default_gateway:
            return default_gateway[1]
            
        interfaces = netifaces.interfaces()
        for iface in interfaces:
            if iface != 'lo':
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    return iface
    except:
        pass
    return None

MODULE_INFO = {
    'name': 'Zmap Scanner',
    'description': 'Scan IP ranges using Zmap (recommended on eth connection)',
    'version': '1.0.0',
    'author': 'Your Name',
    'options': {
        'query_id': {
            'description': 'Query ID to scan (e.g., city_1) or "all" for all ranges. Leave empty if using input_file',
            'required': False,
            'value': None
        },
        'input_file': {
            'description': 'Input file containing target IPs (one per line). If not set, uses query_id',
            'required': False,
            'value': None
        },
        'ports': {
            'description': 'Ports to scan (e.g., 80,443,8080)',
            'required': True,
            'value': None
        },
        'bandwidth': {
            'description': 'Bandwidth in Mbps (e.g., 10M, 100M)',
            'required': False,
            'value': '1M'
        },
        'rate': {
            'description': 'Number of packets per second (e.g., 1000)',
            'required': False,
            'value': '1000'
        },
        'cooldown': {
            'description': 'Cooldown time between scans in seconds',
            'required': False,
            'value': '5'
        },
        'output_file': {
            'description': 'Output file name (default: zmap_results_<timestamp>.txt)',
            'required': False,
            'value': None
        },
        'blacklist': {
            'description': 'Path to IP blacklist file',
            'required': False,
            'value': None
        },
        'interface': {
            'description': 'Network interface to use',
            'required': True,
            'value': get_default_interface()
        }
    }
}

class ZmapScanner:
    def __init__(self):
        self.options = MODULE_INFO['options']
        self.stop_scan = False
        
    def validate_options(self):
        for name, opt in self.options.items():
            if opt['required'] and not opt['value']:
                return False, f"Required option '{name}' is not set"
        
        if not self.options['query_id']['value'] and not self.options['input_file']['value']:
            return False, "Either query_id or input_file must be set"
                
        if not self._check_zmap_installed():
            return False, "Zmap is not installed. Please install it first (sudo apt-get install zmap)"
            
        return True, None
    
    def _check_zmap_installed(self):
        try:
            subprocess.run(['zmap', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False
    
    def _create_target_file(self, ip_list):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as temp:
            for ip in ip_list:
                temp.write(ip + '\n')
        return path
    
    def _build_zmap_command(self, input_file, output_file):
        cmd = ['sudo', 'zmap']
        
        # Add ports
        ports = self.options['ports']['value']
        cmd.extend(['--target-ports', ports])
        
        # Add input file
        cmd.extend(['-w', input_file])
        
        # Add output file
        cmd.extend(['-o', output_file])
        
        # Add required interface
        cmd.extend(['-i', self.options['interface']['value']])
        
        # Add optional parameters
        if self.options['bandwidth']['value']:
            cmd.extend(['-B', self.options['bandwidth']['value']])
            
        if self.options['rate']['value']:
            cmd.extend(['-r', self.options['rate']['value']])
            
        if self.options['blacklist']['value']:
            cmd.extend(['--blacklist-file', self.options['blacklist']['value']])
        
        # Add output format
        cmd.extend(['--output-fields', 'saddr,dport'])
        
        return cmd
    
    def _parse_zmap_output(self, output_file):
        results = []
        try:
            with open(output_file, 'r') as f:
                for line in f:
                    try:
                        ip, port = line.strip().split(',')
                        results.append({
                            'ip': ip,
                            'port': int(port)
                        })
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            return False, f"Error parsing results: {str(e)}"
            
        grouped_results = {}
        for result in results:
            ip = result['ip']
            if ip not in grouped_results:
                grouped_results[ip] = {
                    'ip': ip,
                    'open_ports': set()
                }
            grouped_results[ip]['open_ports'].add(result['port'])
            
        final_results = []
        for ip_data in grouped_results.values():
            ip_data['open_ports'] = sorted(list(ip_data['open_ports']))
            final_results.append(ip_data)
            
        return True, final_results
    
    def run(self, ip_list=None):
        # Reset stop flag
        self.stop_scan = False
        
        # Validate options
        valid, error = self.validate_options()
        if not valid:
            return False, error
            
        try:
            # Determine input file
            target_file = None
            cleanup_target = False
            
            if self.options['input_file']['value']:
                target_file = self.options['input_file']['value']
                if not os.path.exists(target_file):
                    return False, f"Input file not found: {target_file}"
            else:
                if not ip_list:
                    return False, "No IP list provided and no input file specified"
                target_file = self._create_target_file(ip_list)
                cleanup_target = True
            
            if not self.options['output_file']['value']:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'zmap_results_{timestamp}.txt'
            else:
                output_file = self.options['output_file']['value']
            
            cmd = self._build_zmap_command(target_file, output_file)
            
            try:
                print(f"Running command: {' '.join(cmd)}")
                # Run zmap
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                while process.poll() is None:
                    if self.stop_scan:
                        process.terminate()
                        return False, "Scan stopped by user"
                    
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    return False, f"Zmap failed with error: {stderr}"
                
                success, results = self._parse_zmap_output(output_file)
                if not success:
                    return False, results
                
                print(f"\nScan results saved to: {output_file}")
                return True, results
                
            finally:
                if cleanup_target:
                    try:
                        os.unlink(target_file)
                    except:
                        pass
                
        except Exception as e:
            return False, str(e)
    
    def stop(self):
        self.stop_scan = True

def create_instance():
    return ZmapScanner()