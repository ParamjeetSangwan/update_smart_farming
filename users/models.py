# users/models.py
from django.db import models
from django.contrib.auth.models import User
import random
import string
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)
    # ── FEATURE: Avatar Upload ──
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # ── FEATURE: Block/Unban ──
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


class OTPVerification(models.Model):
    """For Email OTP verification on register and 2FA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20)  # 'register', '2fa', 'password_reset'
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # OTP valid for 10 minutes
        return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=10)

    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"{self.user.username} - {self.purpose} - {self.otp}"


class Notification(models.Model):
    """User notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, default='info')  # 'info', 'order', 'announcement', 'alert'
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Announcement(models.Model):
    """Admin announcements to all users"""
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    send_email = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AdminTwoFactor(models.Model):
    """2FA for admin users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    is_enabled = models.BooleanField(default=False)
    last_otp_sent = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - 2FA {'enabled' if self.is_enabled else 'disabled'}"