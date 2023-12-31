# Reticulum-Locus
Tool that scans IP ranges by City/Country/Region names with RustScan.


# Installation
## Requirements
This tool needs a database (I prefer mariadb) and RustScan for scans. I also left a **requirements.txt** for libraries.

[RustScan 2.0.1 for amd64](https://github.com/RustScan/RustScan/releases/download/2.0.1/rustscan_2.0.1_amd64.deb)

[Rustscan 2.0.1 for i386](https://github.com/RustScan/RustScan/releases/download/2.0.1/rustscan_2.0.1_i386.deb)

You need to extract the [zip](https://github.com/setpasslock/Reticulum-Locus/releases) (in assets) file and import the contents to the database or you can get the data [here](https://www.ip2location.com/database/ip2location). There is a script called **installdb.sh** for this.
Then don't forget to enter the connection information with your database in the **db_connect.py** file. 

By the way, this is the sha256 hash of the zip file: 
"`
f3332dfe973b18336e46a44fd7cb6d3a064e519259aaa0da1895568c879074fd
`"




	git clone https://github.com/setpasslock/Reticulum-Locus
    mv ip2location.zip Reticulum-Locus
    cd Reticulum-Locus
    chmod +x installdb.sh
    sudo ./installdb.sh
    pip3 install -r requirements.txt
    sudo python3 locus.py -h


# Usage
You can see and save all IP ranges associated with the city: 

    python3 locus.py -c "San Juan"

You must predefine the ports to be scanned in the IP ranges you choose:
    
    sudo python3 locus.py -c "San Juan" -p 554,80,8080

or you can do a recursive dns scan
    
    python3 locus.py -c "San Juan" -d
