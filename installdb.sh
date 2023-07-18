#!/bin/bash

unzip ip2location.zip;
cd ip2location/;
chown mysql:mysql db.opt ip2location_db11.frm  ip2location_db11.MYD  ip2location_db11.MYI;
cd ..; chown mysql:mysql ip2location
cp -r ip2location /var/lib/mysql/;
sudo systemctl restart mariadb.service;
echo "Database is ready";
