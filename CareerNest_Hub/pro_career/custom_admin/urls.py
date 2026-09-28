from django.urls import path

from . import views


app_name = "custom_admin"

urlpatterns = [
    path("login/", views.admin_login, name="admin_login"),
    path("logout/", views.admin_logout, name="admin_logout"),

    path("", views.admin_dashboard, name="admin_dashboard"),

    path("courses/", views.admin_courses, name="admin_courses"),
    path("manage-courses/", views.admin_courses, name="manage_courses"),
    path("enrollments/", views.admin_enrollments, name="admin_enrollments"),
    path("enrollments/delete/<int:id>/", views.delete_enrollment, name="delete_enrollment"),
    path("jobs/", views.admin_jobs, name="admin_jobs"),
    path("internships/", views.admin_internships, name="admin_internships"),
    path("job-applications/", views.admin_job_applications, name="admin_job_applications"),
    path(
        "internship-applications/",
        views.admin_internship_applications,
        name="admin_internship_applications",
    ),
    path("interviews/", views.admin_interviews, name="admin_interviews"),
    path("interviews/edit/<int:id>/", views.edit_interview, name="edit_interview"),
    path("interviews/delete/<int:id>/", views.delete_interview, name="delete_interview"),
    path("interviews/cancel/<int:id>/", views.cancel_interview, name="cancel_interview"),
    path("recruiters/", views.admin_recruiters, name="admin_recruiters"),
    path("contact-queries/", views.admin_contact_queries, name="admin_contact_queries"),
    path("contact-queries/<int:query_id>/reply/", views.reply_query, name="reply_query"),
    path("add-recruiter/", views.add_recruiter, name="add_recruiter"),
    path("edit-recruiter/<int:id>/", views.edit_recruiter, name="edit_recruiter"),
    path("delete-recruiter/<int:id>/", views.delete_recruiter, name="delete_recruiter"),

    path("add-course/", views.add_course, name="add_course"),
    path("add-lecture/<int:course_id>/", views.add_lecture, name="add_lecture"),
    path("add-job/", views.add_job, name="add_job"),
    path("add-internship/", views.add_internship, name="add_internship"),

    path("courses/edit/<int:id>/", views.edit_course, name="edit_course"),
    path("courses/delete/<int:id>/", views.delete_course, name="delete_course"),

    path("jobs/edit/<int:id>/", views.edit_job, name="edit_job"),
    path("jobs/delete/<int:id>/", views.delete_job, name="delete_job"),

    path("internships/edit/<int:id>/", views.edit_internship, name="edit_internship"),
    path("internships/delete/<int:id>/", views.delete_internship, name="delete_internship"),
]
