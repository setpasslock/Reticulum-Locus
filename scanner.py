import socket
import os

def ptr_dns_scan(target_ip):
    try:
        host_name = socket.gethostbyaddr(target_ip)
        print(f"Reverse DNS lookup for {target_ip}: {host_name[0]}, {host_name[1]}, {host_name[2]}")
    except socket.herror:
        print(f"No reverse DNS record found for {target_ip}")


def RustScan(target_ports=None, city_name=None, first_index=None, second_index=None, index=None):
    hosts_num_final = os.popen("cat hosts.txt|wc -l").read()
    print(f"number of hosts to process {hosts_num_final}")
    result = os.popen(f"sudo rustscan -a 'hosts.txt' -p {target_ports} -b 1000 -g").read()
    print(result)
    print("new result -------------------------------")
    result_dict = {}
    result = result.replace("->",":")
    #print(result)
    
    lines = result.split('\n')

    for line in lines:
        if line:
            parts = line.split(' : ')
            ip = parts[0].strip()
            ports = [int(port.strip()) for port in parts[1].strip('[]').split(',')]
            result_dict[ip] = ports

    #print(result_dict)
    if result != "":
        if index == None:
            with open(f'{city_name}-{first_index}-{second_index}-results_hosts.txt', mode='w') as new_file:
                for ip, ports in result_dict.items():
                    for port in ports:
                        result = new_file.write(f"{ip}:{port}\n")
        else:
            with open(f'{city_name}-{index}-results_hosts.txt', mode='w') as new_file:
                for ip, ports in result_dict.items():
                    for port in ports:
                        result = new_file.write(f"{ip}:{port}\n")
        print("Results are saved")
    else:
        print("Empty Results")
    return result




   
