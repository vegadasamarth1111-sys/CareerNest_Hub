from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from courses.models import Course, Lecture
from .models import MyCourse, CompletedLecture


# =========================
# ENROLL COURSE
# =========================
@login_required
def enroll_course(request, course_id):

    course = get_object_or_404(Course, id=course_id)

    # create only if not exists
    MyCourse.objects.get_or_create(
        user=request.user,
        course=course
    )

    return redirect("my_courses")


# =========================
# MY COURSES PAGE
# =========================
@login_required
def my_courses(request):

    mycourses = MyCourse.objects.filter(
        user=request.user
    ).select_related("course")

    return render(
        request,
        "mycourses/my_courses.html",
        {"courses": mycourses}
    )


# =========================
# WATCH COURSE (PLAYLIST + REAL PROGRESS)
# =========================
@login_required
def watch_course(request, course_id, lecture_id=None):

    course = get_object_or_404(Course, id=course_id)

    mycourse = get_object_or_404(
        MyCourse,
        user=request.user,
        course=course
    )

    lectures = course.lectures.all().order_by("order")

    if lecture_id:
        current_lecture = get_object_or_404(Lecture, id=lecture_id, course=course)
    else:
        current_lecture = lectures.first()

    if current_lecture and request.GET.get("complete"):
        CompletedLecture.objects.get_or_create(
            user=request.user,
            lecture=current_lecture
        )

    total_lectures = lectures.count()

    completed_lectures = CompletedLecture.objects.filter(
        user=request.user,
        lecture__course=course
    ).count()

    if total_lectures > 0:
        progress = int((completed_lectures / total_lectures) * 100)
    else:
        progress = 0

    mycourse.progress = progress
    mycourse.completed = progress == 100
    mycourse.save(update_fields=["progress", "completed"])

    completed_lecture_ids = CompletedLecture.objects.filter(
        user=request.user,
        lecture__course=course
    ).values_list("lecture_id", flat=True)

    context = {
        "course": course,
        "mycourse": mycourse,
        "lectures": lectures,
        "current_lecture": current_lecture,
        "progress": progress,
        "completed_lectures": completed_lecture_ids,
    }

    return render(
        request,
        "mycourses/course_detail.html",
        context
    )
