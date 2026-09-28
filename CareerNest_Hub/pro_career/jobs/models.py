from django.db import models
from django.contrib.auth.models import User
from datetime import date


# Job Model

class Job(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    salary = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    posted_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

    def is_expired(self):
        if self.deadline:
            return self.deadline < date.today()
        return False

# Job Application Model

# Job Application Model
class JobApplication(models.Model):

    STATUS_CHOICES = [
    ("Applied", "Applied"),
    ("Under Review", "Under Review"),
    ("Shortlisted", "Shortlisted"),
    ("Interview Scheduled", "Interview Scheduled"),
    ("Offered", "Offered"),
    ("Hired", "Hired"),
    ("Rejected", "Rejected"),
]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    applied_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Applied'
    )
    # ✅ NEW FIELD
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    interview_date = models.DateField(null=True, blank=True)
    interview_time = models.TimeField(null=True, blank=True)
    interview_mode = models.CharField(max_length=50, null=True, blank=True)
    meeting_link = models.URLField(null=True, blank=True)
    interview_location = models.TextField(null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} applied for {self.job.title}"


class InterviewSchedule(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    MODE_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
    ]

    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interview_schedule",
    )
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interview_schedules",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="interview_schedules",
    )
    interview_date = models.DateField()
    interview_time = models.TimeField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="online")
    location = models.TextField(null=True, blank=True)
    meeting_link = models.URLField(null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-interview_date", "-interview_time"]

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title} ({self.get_status_display()})"
