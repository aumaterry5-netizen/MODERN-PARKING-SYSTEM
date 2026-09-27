from database import connect_database
try:
    connection = connect_database()
    if connection and connection.is_connected():
        print("connected to MySQL successfully!")
        connection.close()
    else:
        print("failed to establish database connection.")
except Exception as e:
    print("connection failed")
    print(e)