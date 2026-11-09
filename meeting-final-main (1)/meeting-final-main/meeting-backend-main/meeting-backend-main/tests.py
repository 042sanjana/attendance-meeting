import socket

try:
    socket.create_connection(("smtp.gmail.com", 587), timeout=10)
    print("SMTP reachable")
except Exception as e:
    print(e)