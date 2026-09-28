from django.db import models
from django.contrib.auth.models import User
from datetime import date


# ================================
# Internship
# ================================

class Internship(models.Model):

    title = models.CharField(
        max_length=200
    )

    company = models.CharField(
        max_length=200
    )

    location = models.CharField(
        max_length=200
    )

    stipend = models.CharField(
        max_length=100
    )

    duration = models.CharField(
        max_length=100
    )

    description = models.TextField()

    posted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posted_internships"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    posted_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )
    deadline = models.DateField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def is_expired(self):
        if self.deadline:
            return self.deadline < date.today()
        return False



# ================================
# Internship Application
# ================================

class InternshipApplication(models.Model):

    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Shortlisted", "Shortlisted"),
        ("Selected", "Selected"),
        ("Rejected", "Rejected"),
    ]

    internship = models.ForeignKey(
        Internship,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="internship_applications"
    )

    resume = models.FileField(
        upload_to="internship_resumes/",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Applied"
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )
    applied_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )
    interview_date = models.DateField(null=True, blank=True)
    interview_time = models.TimeField(null=True, blank=True)
    interview_mode = models.CharField(max_length=50, null=True, blank=True)
    meeting_link = models.URLField(null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-applied_at"]

        # prevent duplicate apply
        unique_together = (
            "internship",
            "applicant",
        )

    def __str__(self):
        return f"{self.applicant.username} -> {self.internship.title}"
