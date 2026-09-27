import mysql.connector

def connect_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="feisty,gee,043",
        database="smart_parking"
    )