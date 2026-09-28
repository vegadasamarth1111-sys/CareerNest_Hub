from django.urls import path
from . import views

app_name = "internships"

urlpatterns = [

    # =========================
    # INTERNSHIP LIST
    # =========================
    path(
        "",
        views.internship_list,
        name="internship_list",
    ),
    path(
        "<int:id>/",
        views.internship_detail,
        name="internship_detail",
    ),

    # =========================
    # APPLY INTERNSHIP
    # =========================
    path(
        "apply/<int:internship_id>/",
        views.apply_internship,
        name="apply_internship",
    ),

    # =========================
    # 🔥 RECRUITER PANEL
    # =========================
    path(
        "recruiter/applications/",
        views.recruiter_internship_applications,
        name="recruiter_internship_applications",
    ),

    # =========================
    # UPDATE STATUS (OPTIONAL 🔥 BEST PRACTICE)
    # =========================
    path(
        "recruiter/update-status/",
        views.recruiter_internship_applications,
        name="update_internship_status",
    ),

    # =========================
    # REVOKE APPLICATION
    # =========================
    path(
        "revoke/<int:app_id>/",
        views.revoke_internship,
        name="revoke_internship",
    ),

]
