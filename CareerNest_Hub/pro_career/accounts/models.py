from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('recruiter', 'Recruiter'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, default='')
    address = models.TextField(blank=True, default='')
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    # Keep company_name to avoid breaking recruiter workflows that depend on it.
    company_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Required for recruiters'
    )

    def __str__(self):
        display_name = self.full_name or self.user.username
        return f"{display_name} - {self.role}"
