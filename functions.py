import ipaddress
targ = []
def find_ip_range(startt_ip,endd_ip):
    start_ip = ipaddress.IPv4Address(startt_ip)
    end_ip = ipaddress.IPv4Address(endd_ip)
    for ip_int in range(int(start_ip), int(end_ip)):
        targ2=ipaddress.IPv4Address(ip_int)
        targ.append(targ2)
    return targ

def save_exit(data):
    with open('iprange-data.txt', mode='w') as new_file:
        for value in data:
            new_file.write(str(value) + '\n')

def save_hosts(data):
    with open('hosts.txt', mode='w') as new_file:
        for value in data:
            new_file.write(str(value) + '\n')


def print_banner():
    banner = """ 
    \033[94m____       __  _            __              \033[0m
   \033[94m/ __ \___  / /_(_)______  __/ /_  ______ ___ \033[0m
  \033[94m/ /_/ / _ \/ __/ / ___/ / / / / / / / __ `__ |\033[0m
 \033[94m/ _, _/  __/ /_/ / /__/ /_/ / / /_/ / / / / / /\033[0m
\033[94m/_/ |_|\___/\__/_/\___/\__,_/_/\__,_/_/ /_/ /_/ \033[0m
                                                
                                          \033[91m__\033[0m                         
      _^_                                \033[91m/ /   ____  _______  _______\033[0m 
      |@| \033[91m---____ ---___                / /   / __ \/ ___/ / / / ___/\033[0m 
     =====              \033[91m---____---__---/ /___/ /_/ / /__/ /_/ (__  ) \033[0m 
      #::                       \033[91m---___/_____/\____/\___/\__,_/____/  \033[0m 
      #::                                       \033[91m****    *****\033[0m
      #::                                           
      #::                                              
      #::                                                       
      #:: 
____-###::^-..     
##############^ \033[94m~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~ ~ ~~ ~~ ~~ ~\033[0m
###############|\033[94m~~ ~~ ~ ~  ~~~~~~~ ~~ ~ ~  ~~~~~~~ ~~ ~ ~  ~~~~~~~ ~~ ~ ~  ~~\033[0m
         
     
      
      
    """
    print(banner)
