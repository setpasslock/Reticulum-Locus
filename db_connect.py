import mysql.connector

def db_connection(first,second):
    db_connect = mysql.connector.connect(
        host="localhost", #change if necessary
        user="", #change it
        password="", #change it
        database="ip2location" #change if necessary
    )
    cursor = db_connect.cursor()
    cursor.execute(f"SELECT ip_from,ip_to FROM ip2location_db11 where {first}='{second}'")
    dcml_ips = cursor.fetchall()
    db_connect.close()
    return dcml_ips
