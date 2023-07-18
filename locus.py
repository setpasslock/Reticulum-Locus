import argparse, socket, struct, time
from prompt_toolkit import prompt
from db_connect import db_connection
from functions import find_ip_range, save_exit, save_hosts, print_banner
from scanner import ptr_dns_scan, RustScan



arg_parser = argparse.ArgumentParser(description="Say Hello")
arg_parser.add_argument("-c", "--city-name", required=False, help="Write the city name: capitalize the first letter: Tokyo")
arg_parser.add_argument("-C", "--country-name", required=False, help="Write the country name: Capitilize the first letter: Thailand")
arg_parser.add_argument("-r", "--region", required=False, help="Write the region name: Capitilize the first letter.")
arg_parser.add_argument("-p", "--ports", required=False, help="Ports to scan")
arg_parser.add_argument("-d", "--dns", action='store_true',required=False, help="Reverse DNS Lookup")
arg_parser.add_argument("-q", "--quite", action='store_true', required=False, help="Don't show banner")


args = vars(arg_parser.parse_args())
city_name = args["city_name"]
country_name = args["country_name"]
region = args["region"]
ports = args["ports"]
dns = args["dns"]
quite = args["quite"]

if ports != None and dns == True:
    print("--dns and --ports scanning cannot occur at the same time")
    exit(0)
else:
    pass

if quite != True:
    print_banner()
    time.sleep(3)
else:
    pass



if city_name != None:
    dcml_ips = db_connection("city_name",city_name)
    i = 0
    list_ip_to = []
    list_ip_from = []
    data = []
    print("\033[91m|------------------------------------------------------|\033[0m")
    for dcml_ip in dcml_ips:

        host_num = dcml_ip[1] - dcml_ip[0] + 1
        v4ip_from = socket.inet_ntoa(struct.pack('!L', dcml_ip[0]))
        v4ip_to = socket.inet_ntoa(struct.pack('!L', dcml_ip[1]))

        list_ip_from.append(v4ip_from)
        list_ip_to.append(v4ip_to)
        print(f"\033[91m|\033[0m\033[94m{i}\033[0m\033[91m|\033[0m{v4ip_from} \033[91m|\033[0m {v4ip_to} \033[91m|\033[0m Host Number: {host_num}    ")
        i = i+1
        data.append(i)
        data.append(list_ip_to)
        data.append(list_ip_from)

    print("\033[91m|------------------------------------------------------|\033[0m")
    print("\033[94m>>>\033[0mThe process of allocating IPs to their ranges is complete. \n\033[94m1)\033[0m If you want to switch to active scan to find out if the hosts are live or not, you can type the \033[94mindex number of the relevant range. \n\033[94m2)\033[0m Write '\033[95mrange\033[0m' if you want to scan ranges between specific indexes. You will then get an input with the starting and ending indexes.\n*** Note that you must have start the scan with \033[91mroot privileges to continue with the active scan.\033[0m ***\n\033[94m3)\033[0m If not, say '\033[95msexit\033[0m' for save and exit or '\033[95mexit\033[0m' for only exit.")

    def decision():
        index = prompt("Decision: ")
        if index == "sexit":
            save_exit(data)
            print("Saved and exited")
            exit(0)
        elif index == "exit":
            print("Not Saved and Exited")
            exit(0)
        elif index == "range":
            first_index = int(prompt("Index From: "))
            fi = first_index
            second_index = int(prompt("Index To: "))
            while first_index < second_index:
                print(f"{first_index}/{second_index} is preparing for scan...")
                target = find_ip_range(list_ip_from[first_index], list_ip_to[first_index])
                tgt = [str(ip) for ip in target]
                save_hosts(tgt)
                first_index += 1

            print("prepare is complete, scan is running")
            if dns == True:
                for i in tgt:
                    ptr_dns_scan(i)
            else:
                RustScan(target_ports=ports,city_name=city_name,first_index=fi, second_index=second_index)

            exit(0)
        else:
            try:
                print(list_ip_from[int(index)], " ", list_ip_to[int(index)])
            except ValueError:
                print("Please \033[95msexit\033[0m, \033[95mexit\033[0m, \033[95mrange\033[0m or \033[94mindex number\033[0m")
                return decision()
        return index

    index = decision()
    target = find_ip_range(list_ip_from[int(index)],list_ip_to[int(index)])
    tgt = [str(ip) for ip in target]
    save_hosts(tgt)
    if dns == True:
        for i in tgt:
            ptr_dns_scan(i)
    elif ports != None:
        RustScan(target_ports=ports, city_name=city_name, index=index)



elif country_name != None:
    dcml_ips = db_connection("country_name",country_name)
    i = 0
    list_ip_to = []
    list_ip_from = []
    data = []
    print("\033[91m|------------------------------------------------------|\033[0m")
    for dcml_ip in dcml_ips:
        host_num = dcml_ip[1] - dcml_ip[0] + 1
        v4ip_from = socket.inet_ntoa(struct.pack('!L', dcml_ip[0]))
        v4ip_to = socket.inet_ntoa(struct.pack('!L', dcml_ip[1]))

        list_ip_from.append(v4ip_from)
        list_ip_to.append(v4ip_to)
        print(
            f"\033[91m|\033[0m\033[94m{i}\033[0m\033[91m|\033[0m{v4ip_from} \033[91m|\033[0m {v4ip_to} \033[91m|\033[0m Host Number: {host_num}    ")
        i = i + 1
        data.append(i)
        data.append(list_ip_to)
        data.append(list_ip_from)

    print("\033[91m|------------------------------------------------------|\033[0m")
    print("\033[94m>>>\033[0mThe process of allocating IPs to their ranges is complete. \n\033[94m1)\033[0m If you want to switch to active scan to find out if the hosts are live or not, you can type the \033[94mindex number of the relevant range. \n\033[94m2)\033[0m Write '\033[95mrange\033[0m' if you want to scan ranges between specific indexes. You will then get an input with the starting and ending indexes.\n*** Note that you must have start the scan with \033[91mroot privileges to continue with the active scan.\033[0m ***\n\033[94m3)\033[0m If not, say '\033[95msexit\033[0m' for save and exit or '\033[95mexit\033[0m' for only exit.")


    def decision():
        index = prompt("Decision: ")
        if index == "sexit":
            save_exit(data)
            print("Saved and exited")
            exit(0)
        elif index == "exit":
            print("Not Saved and Exited")
            exit(0)
        elif index == "range":
            first_index = int(prompt("Index From: "))
            fi = first_index
            second_index = int(prompt("Index To: "))
            while first_index < second_index:
                print(f"{first_index}/{second_index} is preparing for scan...")
                target = find_ip_range(list_ip_from[first_index], list_ip_to[first_index])
                tgt = [str(ip) for ip in target]
                save_hosts(tgt)
                first_index += 1

            print("prepare is complete, scan is running")
            if dns == True:
                for i in tgt:
                    ptr_dns_scan(i)
            else:
                RustScan(target_ports=ports, city_name=city_name, first_index=fi, second_index=second_index)

            exit(0)
        else:
            try:
                print(list_ip_from[int(index)], " ", list_ip_to[int(index)])
            except ValueError:
                print("Please \033[95msexit\033[0m, \033[95mexit\033[0m, \033[95mrange\033[0m or \033[94mindex number\033[0m")
                return decision()
        return index


    index = decision()
    target = find_ip_range(list_ip_from[int(index)], list_ip_to[int(index)])
    tgt = [str(ip) for ip in target]
    save_hosts(tgt)
    if dns == True:
        for i in tgt:
            ptr_dns_scan(i)
    else:
        RustScan(target_ports=ports, city_name=city_name, index=index)



elif region != None:
    dcml_ips = db_connection("region_name", region)
    i = 0
    list_ip_to = []
    list_ip_from = []
    data = []
    print("\033[91m|------------------------------------------------------|\033[0m")
    for dcml_ip in dcml_ips:
        host_num = dcml_ip[1] - dcml_ip[0] + 1
        v4ip_from = socket.inet_ntoa(struct.pack('!L', dcml_ip[0]))
        v4ip_to = socket.inet_ntoa(struct.pack('!L', dcml_ip[1]))

        list_ip_from.append(v4ip_from)
        list_ip_to.append(v4ip_to)
        print(
            f"\033[91m|\033[0m\033[94m{i}\033[0m\033[91m|\033[0m{v4ip_from} \033[91m|\033[0m {v4ip_to} \033[91m|\033[0m Host Number: {host_num}    ")
        i = i + 1
        data.append(i)
        data.append(list_ip_to)
        data.append(list_ip_from)

    print("\033[91m|------------------------------------------------------|\033[0m")
    print("\033[94m>>>\033[0mThe process of allocating IPs to their ranges is complete. \n\033[94m1)\033[0m If you want to switch to active scan to find out if the hosts are live or not, you can type the \033[94mindex number of the relevant range. \n\033[94m2)\033[0m Write '\033[95mrange\033[0m' if you want to scan ranges between specific indexes. You will then get an input with the starting and ending indexes.\n*** Note that you must have start the scan with \033[91mroot privileges to continue with the active scan.\033[0m ***\n\033[94m3)\033[0m If not, say '\033[95msexit\033[0m' for save and exit or '\033[95mexit\033[0m' for only exit.")


    def decision():
        index = prompt("Decision: ")
        if index == "sexit":
            save_exit(data)
            print("Saved and exited")
            exit(0)
        elif index == "exit":
            print("Not Saved and Exited")
            exit(0)
        elif index == "range":
            first_index = int(prompt("Index From: "))
            fi = first_index
            second_index = int(prompt("Index To: "))
            while first_index < second_index:
                print(f"{first_index}/{second_index} is preparing for scan...")
                target = find_ip_range(list_ip_from[first_index], list_ip_to[first_index])
                tgt = [str(ip) for ip in target]
                save_hosts(tgt)
                first_index += 1

            print("Prepare is complete, scan is running")
            if dns == True:
                for i in tgt:
                    ptr_dns_scan(i)
            else:
                RustScan(target_ports=ports, city_name=city_name, first_index=fi, second_index=second_index)

            exit(0)
        else:
            try:
                print(list_ip_from[int(index)], " ", list_ip_to[int(index)])
            except ValueError:
                print("Please \033[95msexit\033[0m, \033[95mexit\033[0m, \033[95mrange\033[0m or \033[94mindex number\033[0m")
                return decision()
        return index


    index = decision()
    target = find_ip_range(list_ip_from[int(index)], list_ip_to[int(index)])
    tgt = [str(ip) for ip in target]
    save_hosts(tgt)
    if dns == True:
        for i in tgt:
            ptr_dns_scan(i)
    else:
        RustScan(target_ports=ports, city_name=city_name, index=index)
