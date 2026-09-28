from django.urls import path
from .views import my_courses, enroll_course, watch_course


urlpatterns = [

    # =========================
    # MY COURSES PAGE
    # =========================
    path(
        "",
        my_courses,
        name="my_courses"
    ),

    # =========================
    # ENROLL COURSE
    # =========================
    path(
        "enroll/<int:course_id>/",
        enroll_course,
        name="enroll_course"
    ),

    # =========================
    # COURSE DETAIL + PLAYLIST
    # =========================
    path(
        "course/<int:course_id>/",
        watch_course,
        name="course_detail"
    ),
    path(
        "course/<int:course_id>/<int:lecture_id>/",
        watch_course,
        name="course_detail_lecture"
    ),

    # =========================
    # LEGACY WATCH ROUTES
    # =========================
    path(
        "watch/<int:course_id>/",
        watch_course,
        name="watch_course"
    ),
    path(
        "watch/<int:course_id>/<int:lecture_id>/",
        watch_course,
        name="watch_lecture"
    ),
]
