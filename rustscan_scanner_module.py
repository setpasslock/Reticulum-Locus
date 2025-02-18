import subprocess
import tempfile
import os
from datetime import datetime
import re

MODULE_INFO = {
    'name': 'RustScan Scanner',
    'description': 'Scan IP ranges using RustScan',
    'version': '1.0.0',
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
            'description': 'Ports to scan (e.g., 80,443,8080) or ranges (e.g., 1-1000)',
            'required': True,
            'value': None
        },
        'timeout': {
            'description': 'Timeout for each port scan in milliseconds (e.g., 2000)',
            'required': False,
            'value': '2500'
        },
        'batch_size': {
            'description': 'Batch size for parallel scanning (e.g., 2500)',
            'required': False,
            'value': '2500'
        },
        'ulimit': {
            'description': 'Maximum number of open files (e.g., 5000)',
            'required': False,
            'value': '5000'
        },
        'tries': {
            'description': 'Number of tries before timeout (e.g., 2)',
            'required': False,
            'value': '2'
        },
        'output_file': {
            'description': 'Output file name (default: rustscan_results_<timestamp>.txt)',
            'required': False,
            'value': None
        }
    }
}

class RustScanScanner:
    def __init__(self):
        self.options = MODULE_INFO['options']
        
    def validate_options(self):
        for name, opt in self.options.items():
            if opt['required'] and not opt['value']:
                return False, f"Required option '{name}' is not set"
        
        if not self.options['query_id']['value'] and not self.options['input_file']['value']:
            return False, "Either query_id or input_file must be set"
            
        return True, None
    
    def _create_target_file(self, ip_list):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as temp:
            for ip in ip_list:
                temp.write(ip + '\n')
        return path
    
    def _build_rustscan_command(self, input_file):
        cmd = ['rustscan']
        
        # Add addresses file
        cmd.extend(['--addresses', input_file])
        
        # Add ports
        ports = self.options['ports']['value']
        cmd.extend(['--ports', ports])
        
        # Add optional parameters
        if self.options['timeout']['value']:
            cmd.extend(['--timeout', self.options['timeout']['value']])
            
        if self.options['batch_size']['value']:
            cmd.extend(['--batch-size', self.options['batch_size']['value']])
            
        if self.options['ulimit']['value']:
            cmd.extend(['--ulimit', self.options['ulimit']['value']])
            
        if self.options['tries']['value']:
            cmd.extend(['--tries', self.options['tries']['value']])
        
        return cmd
    
    def run(self, ip_list=None):
        valid, error = self.validate_options()
        if not valid:
            return False, error
            
        try:
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
                output_file = f'rustscan_results_{timestamp}.txt'
            else:
                output_file = self.options['output_file']['value']
            
            cmd = self._build_rustscan_command(target_file)
            
            try:
                print(f"Running command: {' '.join(cmd)}")
                
                with open(output_file, 'w') as outfile:
                    # Start process
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    results = []
                    current_ip = None
                    current_ports = set()
                    
                    # İlk satır kontrolü için flag
                    first_line_checked = False
                    ip_port_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$"
                    
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            if line.startswith('Open'):
                                ip_port = line.split('Open ')[1].strip()
                                
                                print(ip_port)
                                
                                if not first_line_checked:
                                    first_line_checked = True
                                    if not re.match(ip_port_pattern, ip_port):
                                        continue  # İlk satır uygun formatta değilse kaydetme
                                
                                outfile.write(ip_port + '\n')
                                outfile.flush()
                            
                            if "Port" in line and "is open on" in line:
                                try:
                                    parts = line.split()
                                    port = int(parts[1])
                                    ip = parts[-1]
                                    
                                    if current_ip != ip:
                                        if current_ip and current_ports:
                                            results.append({
                                                'ip': current_ip,
                                                'open_ports': sorted(list(current_ports))
                                            })
                                        current_ip = ip
                                        current_ports = set()
                                    
                                    current_ports.add(port)
                                except (ValueError, IndexError):
                                    continue
                    
                    if current_ip and current_ports:
                        results.append({
                            'ip': current_ip,
                            'open_ports': sorted(list(current_ports))
                        })
                    
                    _, stderr = process.communicate()
                    
                    if process.returncode != 0 and not results:
                        return False, f"RustScan failed with error: {stderr}"
                    
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

def create_instance():
    return RustScanScanner()