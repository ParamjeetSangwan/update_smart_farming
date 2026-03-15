from django.db import models
from django.contrib.auth.models import User

class Tool(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.FloatField()
    category = models.CharField(max_length=100, default='General')
    # Image optional
    image = models.ImageField(upload_to='tools/', blank=True, null=True)

    def __str__(self):
        return self.name


class Pesticide(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.FloatField()
    # Image optional
    image = models.ImageField(upload_to='pesticides/', blank=True, null=True)

    def __str__(self):
        return self.name
