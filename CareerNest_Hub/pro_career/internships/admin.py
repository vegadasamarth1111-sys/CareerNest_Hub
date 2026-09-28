# Register your models here.
from django.contrib import admin
from .models import Internship, InternshipApplication


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "location",
        "duration",
        "posted_date",
        "deadline",
        "created_at",
    )


@admin.register(InternshipApplication)
class InternshipApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "applicant",
        "internship",
        "status",
        "applied_date",
        "applied_at",
    )
