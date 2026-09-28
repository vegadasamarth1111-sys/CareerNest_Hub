from django.urls import path
from . import views

urlpatterns = [
    # Show all jobs
    path("", views.jobs_list, name="jobs_list"),

    # Backward-compatible recruiter URL
    # Supports old links like /jobs/recruiter/
    path("recruiter/", views.recruiter_applications, name="recruiter_dashboard"),

    # Job detail page
    path("<int:id>/", views.job_detail, name="job_detail"),

    # Apply for job
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),

    # My Applications page
    path("my-applications/", views.my_applications, name="my_applications"),

    # Revoke application (student)
    path(
        "revoke/<int:app_id>/",
        views.revoke_application,
        name="revoke_application"
    ),

    # Backward-compatible withdraw route
    path(
        "withdraw/<int:app_id>/",
        views.withdraw_application,
        name="withdraw_application"
    ),
    path('applicants/<int:job_id>/', views.job_applicants, name='job_applicants'),
    path('recruiter/applications/', views.recruiter_applications, name='recruiter_applications'),
    path('schedule-interview/<int:id>/', views.schedule_interview, name='schedule_interview'),


]
