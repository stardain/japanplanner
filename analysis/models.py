from django.db import connections
from django.db.utils import OperationalError
from dotenv import load_dotenv

load_dotenv()

db_conn = connections['default']
try:
    c = db_conn.cursor()
    print("Database connection successful!")
except OperationalError as e:
    print(f"Database connection failed: {e}")
finally:
    db_conn.close()