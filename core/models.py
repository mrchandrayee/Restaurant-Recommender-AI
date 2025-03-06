from django.db import models
from django.contrib.auth.models import User

class Restaurant(models.Model):
    PRICE_CHOICES = [
        ('$', 'Budget'),
        ('$$', 'Moderate'),
        ('$$$', 'Expensive'),
        ('$$$$', 'Very Expensive'),
    ]
    
    ATMOSPHERE_CHOICES = [
        ('romantic', 'Romantic'),
        ('casual', 'Casual'),
        ('formal', 'Formal'),
        ('family', 'Family-Friendly'),
        ('trendy', 'Trendy'),
        ('business', 'Business'),
    ]

    name = models.CharField(max_length=200)
    address = models.TextField()
    cuisine_type = models.CharField(max_length=100)
    price_range = models.CharField(max_length=4, choices=PRICE_CHOICES)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    capacity = models.IntegerField(default=50)
    operating_hours = models.JSONField(default=dict)
    dietary_options = models.JSONField(default=list)
    atmosphere = models.CharField(max_length=20, choices=ATMOSPHERE_CHOICES, default='casual')
    average_dining_time = models.IntegerField(default=60, help_text="Average dining time in minutes")
    noise_level = models.CharField(max_length=20, choices=[
        ('quiet', 'Quiet'),
        ('moderate', 'Moderate'),
        ('loud', 'Loud')
    ], default='moderate')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Review(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('restaurant', 'user')

    def __str__(self):
        return f"{self.user.username}'s review for {self.restaurant.name}"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party_size = models.IntegerField()
    reservation_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s reservation at {self.restaurant.name}"
