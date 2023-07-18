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

    if index == None:
        with open(f'{city_name}-{first_index}-{second_index}-results_hosts.txt', mode='w') as new_file:
            new_file.write(str(result) + '\n')
    else:
        with open(f'{city_name}-{index}-results_hosts.txt', mode='w') as new_file:
                new_file.write(str(result) + '\n')

    print("Results are saved")
    return result
