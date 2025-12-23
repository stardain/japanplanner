from django.db import connections
from django.db import models
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

class StationInfo(models.Model):
    station_id = models.CharField(primary_key=True, max_length=4)
    station_fullname = models.CharField(max_length=35, blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'station_info'
    
class StationNeighbours(models.Model):
    pk = models.CompositePrimaryKey('station_id', 'station_neighbour')
    station_id = models.CharField(max_length=4)
    station_neighbour = models.CharField(max_length=4)
    time = models.IntegerField(blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'station_neighbours'
