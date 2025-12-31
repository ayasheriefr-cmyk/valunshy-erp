
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    # Connect to the default 'postgres' database
    try:
        con = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            host='127.0.0.1',
            password='radwa01000'
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'gold_erp_db'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database gold_erp_db...")
            cur.execute('CREATE DATABASE gold_erp_db')
            print("Database created successfully!")
        else:
            print("Database gold_erp_db already exists.")
            
        cur.close()
        con.close()
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    create_database()
