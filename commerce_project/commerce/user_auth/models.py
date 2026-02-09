from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
