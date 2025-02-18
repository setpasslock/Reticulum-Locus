import argparse
import shlex
import ipaddress
from rich.console import Console
from rich.table import Table
from rich import box
from dbmanager import IP2LocationUpdater
from ip2location_query import IP2LocationQuery
from config import IP2LOCATION_TOKEN
from ui_console import InteractiveConsole
from colorama import init, Fore, Style


def calculate_ip_stats(ip_from, ip_to):
    start_ip = ipaddress.IPv4Address(ip_from)
    end_ip = ipaddress.IPv4Address(ip_to)
    
    total_hosts = int(end_ip) - int(start_ip) + 1
    
    return {
        'total_hosts': total_hosts
    }

def display_results(results):
    console = Console()
    
    table = Table(show_header=True, header_style="bold magenta", box=box.DOUBLE_EDGE)
    table.add_column("#", style="dim")
    table.add_column("IP Range", style="cyan")
    table.add_column("Total Hosts", style="green")
    table.add_column("City", style="green")
    table.add_column("Region", style="blue")
    table.add_column("Country", style="yellow")
    table.add_column("Country Code", style="red")
    
    total_ranges = 0
    total_hosts = 0
    
    for idx, row in enumerate(results, 1):
        ip_from = str(ipaddress.IPv4Address(row['ip_from']))
        ip_to = str(ipaddress.IPv4Address(row['ip_to']))
        ip_range = f"{ip_from} - {ip_to}"
        
        stats = calculate_ip_stats(row['ip_from'], row['ip_to'])
        total_ranges += 1
        total_hosts += stats['total_hosts']
        
        table.add_row(
            str(idx),
            ip_range,
            f"{stats['total_hosts']:,}",
            row['city_name'] or '-',
            row['region_name'] or '-',
            row['country_name'] or '-',
            row['country_code'] or '-'
        )
    
    console.print(table)
    
    summary = Table(show_header=False, box=box.SIMPLE)
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="yellow")
    
    summary.add_row("Total IP Ranges", f"{total_ranges:,}")
    summary.add_row("Total Host Addresses", f"{total_hosts:,}")
    
    console.print("\n[bold]Summary Statistics:[/bold]")
    console.print(summary)

def process_args(args_str=None):
    parser = argparse.ArgumentParser(description='IP Range Scanner by Location')
    parser.add_argument('--update', action='store_true', help='Update IP2Location database')
    parser.add_argument('--city', help='Search by city name')
    parser.add_argument('--country', help='Search by country name')
    parser.add_argument('--country-code', help='Search by country code (e.g., US, TR)')
    parser.add_argument('--region', help='Search by region/state name')
    
    if args_str:
        try:
            args = parser.parse_args(shlex.split(args_str))
        except Exception:
            return None
    else:
        args = parser.parse_args()
    
    return args

def handle_command(args, console=None):
    if not args:
        return
    
    try:
        updater = IP2LocationUpdater()
        
        if args.update:
            print("[*] Updating IP2Location database...")
            if updater.update_database(IP2LOCATION_TOKEN):
                print("[+] Database updated successfully")
            else:
                print("[*] Database is already up to date")
            return
        
        if not updater.ensure_database_exists(IP2LOCATION_TOKEN):
            print("[-] Failed to create/verify database")
            return
        
        query = IP2LocationQuery()
        results = None
        query_type = None
        query_value = None
        
        if args.city:
            results = query.search_by_city(args.city)
            query_type = 'city'
            query_value = args.city
        elif args.country:
            results = query.search_by_country_name(args.country)
            query_type = 'country'
            query_value = args.country
        elif args.country_code:
            results = query.search_by_country_code(args.country_code)
            query_type = 'country_code'
            query_value = args.country_code
        elif args.region:
            results = query.search_by_region(args.region)
            query_type = 'region'
            query_value = args.region
        
        if results:
            display_results(results)
            if console:
                console.store_query_results(query_type, query_value, results)
        else:
            print("[-] No results found")
            
    except Exception as e:
        print(f"[-] Error: {str(e)}")



def print_banner():
    init()
    
    banner = f""" 
    {Fore.BLUE}____       __  _            __              {Style.RESET_ALL}
   {Fore.BLUE}/ __ \\___  / /_(_)______  __/ /_  ______ ___ {Style.RESET_ALL}
  {Fore.BLUE}/ /_/ / _ \\/ __/ / ___/ / / / / / / / __ `__ |{Style.RESET_ALL}
 {Fore.BLUE}/ _, _/  __/ /_/ / /__/ /_/ / / /_/ / / / / / /{Style.RESET_ALL}
{Fore.BLUE}/_/ |_|\\___/\\__/_/\\___/\\__,_/_/\\__,_/_/ /_/ /_/ {Style.RESET_ALL}
                                                
                                          {Fore.RED}__{Style.RESET_ALL}                         
      _^_                                {Fore.RED}/ /   ____  _______  _______{Style.RESET_ALL} 
      |@| {Fore.RED}---____ ---___                / /   / __ \\/ ___/ / / / ___/{Style.RESET_ALL} 
     =====              {Fore.RED}---____---__---/ /___/ /_/ / /__/ /_/ (__  ) {Style.RESET_ALL} 
      #::                       {Fore.RED}---___/_____/\\____/\\___/\\__,_/____/  {Style.RESET_ALL} 
      #::                                       {Fore.RED}****    *****{Style.RESET_ALL}
      #::                                           
      #::                                              
      #::                                                       
      #:: 
____-###::^-..     
##############^ {Fore.BLUE}~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~{Style.RESET_ALL}
###############|{Fore.BLUE}~~ ~~ ~ ~  ~~~~~~~ ~~ ~ ~  ~~~~~~~ ~~ ~ ~  ~~~~~~~ ~~ ~ ~  ~~{Style.RESET_ALL}
    """
    print(banner)

def main():
    args = process_args()
    console = InteractiveConsole()
    
    if args and (args.city or args.country or args.country_code or args.region or args.update):
        handle_command(args, console)
    else:
        print_banner()
    
    while True:
        
        command = console.run()
        if command is None:  
            break
        args = process_args(command)
        if args:
            handle_command(args, console)

if __name__ == "__main__":
    main()