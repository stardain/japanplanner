from django.db import connections
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.utils import OperationalError
from django.conf import settings
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

class CustomUser(AbstractUser):
    # This creates the actual database table
    class Meta:
        db_table = 'user_info'

class SavedRestaurant(models.Model):
    # CHANGE THIS: Remove ForeignKey, add ManyToMany
    #users = models.ManyToManyField(
    #    settings.AUTH_USER_MODEL,
    #    through='UserToRestaurant',
    #    related_name='saved_restaurants'
    #)
    
    # Keep the rest of your fields exactly as they are...
    name = models.CharField(max_length=500)
    link = models.URLField(max_length=500, unique=True) # Add unique=True here!
    main_pic = models.URLField(max_length=500, blank=True) # Link to the image
    
    # Rating (Using Decimal for 4.5, 4.8, etc.)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    
    # Locations & Logistics
    station = models.CharField(max_length=500, blank=True)
    fee = models.CharField(max_length=500, blank=True) # Usually text like "¥1000-2000"
    
    # Hours (TextField is safer for varying list formats)
    open_hours = models.TextField(blank=True) 
    closed_on = models.CharField(max_length=500, blank=True)
    
    # Descriptions
    short_desc = models.TextField(null=True, blank=True) 
    long_desc = models.TextField(blank=True) # Full details
    
    # Metadata
    added_on = models.DateTimeField(auto_now_add=True)

    time = models.TextField(null=True, blank=True)

# In models.py
    def __str__(self):
        return self.name  # Simplified because many users now own one restaurant

    class Meta:
        db_table = 'saved_restaurants'

class UserToRestaurant(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(SavedRestaurant, on_delete=models.CASCADE)
    
    # THIS is where the user-specific data lives
    travel_time = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents the same user from saving the same restaurant twice
        unique_together = ('user', 'restaurant')