# orders/models.py

from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.FloatField(default=0)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    item_type = models.CharField(max_length=50, default="tool")  # added default
    item_id = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=100, default="unknown")   # added default
    price = models.FloatField(default=0)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name} x {self.quantity}"