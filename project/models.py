from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()
User = settings.AUTH_USER_MODEL


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    owner           = models.ForeignKey(User, on_delete=models.CASCADE)
    name            = models.CharField(max_length=100)
    brand           = models.CharField(max_length=100)
    category        = models.ForeignKey(Category, on_delete=models.CASCADE)
    shade           = models.CharField(max_length=100)
    price           = models.DecimalField(max_digits=6, decimal_places=2)
    image           = models.ImageField(upload_to='product_images/', blank=True, null=True)
    expiration_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.shade})"

    @property
    def days_until_expiration(self):
        return (self.expiration_date - date.today()).days

    @property
    def is_expiring_soon(self):
        return self.days_until_expiration <= 7


class Routine(models.Model):
    owner       = models.ForeignKey(User, on_delete=models.CASCADE)
    name        = models.CharField(max_length=100)
    date        = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class RoutineItem(models.Model):
    routine    = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name='items')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE)
    step_order = models.PositiveIntegerField()
    notes      = models.TextField(blank=True)

    class Meta:
        ordering = ['step_order']

    def __str__(self):
        return f"{self.product.name} (Step {self.step_order})"


class Favorite(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"


class Review(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating     = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    text       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} – {self.product.name} ({self.rating})"


class UsageLog(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='usage_logs')
    date    = models.DateField(default=date.today)

    class Meta:
        unique_together = ('user', 'product', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} used {self.product.name} on {self.date}"
class Follow(models.Model):
    follower   = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    followee   = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followee')

    def __str__(self):
        return f"{self.follower.username} → {self.followee.username}"