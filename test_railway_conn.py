import os
import psycopg2
from urllib.parse import urlparse

url = "postgresql://postgres:KtZKTedzjfXfTgYrIEhGPZugJKBYGmVe@crossover.proxy.rlwy.net:40385/railway"
result = urlparse(url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

try:
    conn = psycopg2.connect(
        database = database,
        user = username,
        password = password,
        host = hostname,
        port = port
    )
    print("Connection successful!")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone())
    conn.close()
except Exception as e:
    print(f"Error: {e}")
