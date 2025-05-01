"""
models.py

This file defines the database models for the application, including:
- User-related models
- Product and category management
- Routine and routine items
- Favorites, reviews, usage logs, and follow system

Models use Django’s ORM system and support relationships between users, products, and routines.
"""

from django.db import models
from django.conf import settings
from datetime import date

# Get the User model from Django settings
User = settings.AUTH_USER_MODEL


# Category model (e.g., skincare, makeup, haircare)
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Product model representing an individual product in the system
class Product(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)  # user who owns the product
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # category (foreign key)
    shade = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    expiration_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.shade})"

    @property
    def days_until_expiration(self):
        # Calculate days remaining until expiration
        return (self.expiration_date - date.today()).days

    @property
    def is_expiring_soon(self):
        # Returns True if product expires within the next 7 days
        return self.days_until_expiration <= 7


# Routine model (collection of products used together on a certain date)
class Routine(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)  # owner of the routine
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True)  # optional routine description

    def __str__(self):
        return self.name


# RoutineItem model (individual product steps within a routine)
class RoutineItem(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='items')  # parent routine
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # product in the routine
    step_order = models.PositiveIntegerField()  # order of application
    notes = models.TextField(blank=True)  # optional notes

    class Meta:
        ordering = ['step_order']  # default order when retrieving items

    def __str__(self):
        return f"{self.product.name} (Step {self.step_order})"


# Favorite model (track which products a user has favorited)
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')  # user who favorited
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')  # favorited product
    created_at = models.DateTimeField(auto_now_add=True)  # when it was favorited

    class Meta:
        unique_together = ('user', 'product')  # prevent duplicate favorites

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"


# Review model (user-submitted reviews on products)
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')  # reviewed product
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')  # reviewer
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # rating 1–5
    text = models.TextField(blank=True)  # optional review text
    created_at = models.DateTimeField(auto_now_add=True)  # when review was posted

    class Meta:
        unique_together = ('product', 'user')  # one review per user per product
        ordering = ['-created_at']  # newest reviews first

    def __str__(self):
        return f"{self.user.username} – {self.product.name} ({self.rating})"


# UsageLog model (track product usage per user per day)
class UsageLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # user who used the product
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='usage_logs')  # used product
    date = models.DateField(default=date.today)  # date of usage

    class Meta:
        unique_together = ('user', 'product', 'date')  # one log per day per product
        ordering = ['-date']  # newest logs first

    def __str__(self):
        return f"{self.user.username} used {self.product.name} on {self.date}"


# Follow model (track user-to-user following relationships)
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')  # user who follows
    followee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')  # user being followed
    created_at = models.DateTimeField(auto_now_add=True)  # when follow happened

    class Meta:
        unique_together = ('follower', 'followee')  # prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} → {self.followee.username}"
