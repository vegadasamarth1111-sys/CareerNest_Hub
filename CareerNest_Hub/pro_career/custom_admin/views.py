from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from datetime import datetime
from types import SimpleNamespace

from accounts.models import Profile
from dashboard.models import ContactQuery
from .forms import CourseForm, InternshipForm, JobForm, LectureForm
from courses.models import Course, Enrollment
from internships.models import Internship, InternshipApplication
from jobs.models import Job, JobApplication, InterviewSchedule


User = get_user_model()


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("custom_admin:admin_login")

        if not request.user.is_superuser:
            return redirect("/dashboard/")

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect("custom_admin:admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("custom_admin:admin_dashboard")

        return render(
            request,
            "custom_admin/admin_login.html",
            {"error": "Invalid admin credentials"},
        )

    return render(request, "custom_admin/admin_login.html")


def admin_logout(request):
    logout(request)
    return redirect("custom_admin:admin_login")


def _recruiter_queryset():
    return (
        User.objects.select_related("profile")
        .filter(is_superuser=False)
        .filter(Q(is_staff=True) | Q(profile__role="recruiter"))
        .distinct()
    )


def _sync_recruiter_profile(user, company_name=""):
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.role = "recruiter"
    profile.email = user.email or ""
    profile.company_name = (company_name or "").strip()
    profile.save()
    return profile


@admin_required
def admin_dashboard(request):
    job_applications = JobApplication.objects.select_related(
        "user",
        "job",
    ).order_by("-applied_at")[:5]

    internship_applications = InternshipApplication.objects.select_related(
        "applicant",
        "internship",
    ).order_by("-applied_at")[:5]

    context = {
        "total_users": User.objects.count(),
        "total_courses": Course.objects.count(),
        "total_jobs": Job.objects.count(),
        "total_internships": Internship.objects.count(),
        "job_applications": job_applications,
        "internship_applications": internship_applications,
    }
    return render(request, "custom_admin/dashboard.html", context)


@admin_required
def admin_courses(request):
    courses = Course.objects.all().order_by("-created_at")
    return render(request, "custom_admin/manage_courses.html", {"courses": courses})


@admin_required
def admin_enrollments(request):
    search_query = request.GET.get("search", "").strip()
    course_filter = request.GET.get("course", "All")
    level_filter = request.GET.get("level", "All")

    enrollments = (
        Enrollment.objects.filter(is_paid=True)
        .select_related("user", "course")
        .order_by("-enrolled_at")
    )

    if search_query:
        enrollments = enrollments.filter(
            Q(user__username__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(course__title__icontains=search_query)
        )

    selected_course_id = None
    if course_filter != "All":
        try:
            selected_course_id = int(course_filter)
            enrollments = enrollments.filter(course_id=selected_course_id)
        except (TypeError, ValueError):
            selected_course_id = None

    level_values = [choice[0] for choice in Course.LEVEL_CHOICES]
    if level_filter != "All" and level_filter in level_values:
        enrollments = enrollments.filter(course__level=level_filter)

    course_options = Course.objects.filter(
        id__in=Enrollment.objects.filter(is_paid=True).values_list("course_id", flat=True)
    ).order_by("title")

    context = {
        "enrollments": enrollments,
        "search_query": search_query,
        "course_options": course_options,
        "selected_course_id": selected_course_id,
        "level_choices": Course.LEVEL_CHOICES,
        "selected_level": level_filter,
        "total_enrollments": enrollments.count(),
    }
    return render(request, "custom_admin/enrollments.html", context)


@admin_required
@require_POST
def delete_enrollment(request, id):
    enrollment = get_object_or_404(Enrollment, id=id, is_paid=True)
    enrollment.delete()
    messages.success(request, "Enrollment deleted successfully.")
    return redirect("custom_admin:admin_enrollments")


@admin_required
def add_course(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("custom_admin:admin_courses")
    else:
        form = CourseForm()

    return render(request, "custom_admin/add_course.html", {"form": form})


@admin_required
def add_lecture(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        form = LectureForm(request.POST, request.FILES)
        form.instance.course = course
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.course = course
            lecture.save()
            return redirect("custom_admin:manage_courses")
    else:
        form = LectureForm(initial={"course": course.id})

    return render(
        request,
        "custom_admin/add_lecture.html",
        {
            "form": form,
            "course": course,
        },
    )


@admin_required
def edit_course(request, id):
    course = get_object_or_404(Course, id=id)

    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.fields.get("created_at"):
            form.fields["created_at"].disabled = True
            form.fields["created_at"].widget.attrs["readonly"] = True

        if form.is_valid():
            form.save()
            return redirect("custom_admin:admin_courses")
    else:
        form = CourseForm(instance=course)
        if form.fields.get("created_at"):
            form.fields["created_at"].disabled = True
            form.fields["created_at"].widget.attrs["readonly"] = True

    return render(
        request,
        "custom_admin/edit_course.html",
        {
            "course": course,
            "form": form,
        },
    )


@admin_required
def delete_course(request, id):
    course = get_object_or_404(Course, id=id)
    course.delete()
    return redirect("custom_admin:admin_courses")


@admin_required
def admin_jobs(request):
    jobs = Job.objects.all().order_by("-created_at")
    return render(request, "custom_admin/manage_jobs.html", {"jobs": jobs})


@admin_required
def add_job(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("custom_admin:admin_jobs")
    else:
        form = JobForm()

    return render(
        request,
        "custom_admin/add_job.html",
        {
            "form": form,
            "show_requirements": "requirements" in form.fields,
            "show_job_type": "job_type" in form.fields,
            "show_experience_level": "experience_level" in form.fields,
        },
    )


@admin_required
def edit_job(request, id):
    job = get_object_or_404(Job, id=id)

    if request.method == "POST":
        job.title = request.POST.get("title", job.title).strip()
        job.company = request.POST.get("company", job.company).strip()
        job.location = request.POST.get("location", job.location).strip()
        job.salary = request.POST.get("salary", job.salary).strip()
        job.description = request.POST.get("description", job.description).strip()
        job.save()

        return redirect("custom_admin:admin_jobs")

    return render(request, "custom_admin/edit_job.html", {"job": job})


@admin_required
def delete_job(request, id):
    job = get_object_or_404(Job, id=id)
    job.delete()
    return redirect("custom_admin:admin_jobs")


@admin_required
def admin_internships(request):
    internships = Internship.objects.all().order_by("-created_at")
    return render(
        request,
        "custom_admin/manage_internships.html",
        {"internships": internships},
    )


@admin_required
def add_internship(request):
    if request.method == "POST":
        form = InternshipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("custom_admin:admin_internships")
    else:
        form = InternshipForm()

    return render(
        request,
        "custom_admin/add_internship.html",
        {
            "form": form,
            "show_skills_required": "skills_required" in form.fields,
        },
    )


@admin_required
def edit_internship(request, id):
    internship = get_object_or_404(Internship, id=id)

    if request.method == "POST":
        internship.title = request.POST.get("title", internship.title).strip()
        internship.company = request.POST.get("company", internship.company).strip()
        internship.location = request.POST.get("location", internship.location).strip()
        internship.stipend = request.POST.get("stipend", internship.stipend).strip()
        internship.duration = request.POST.get("duration", internship.duration).strip()
        internship.description = request.POST.get("description", internship.description).strip()
        internship.save()

        return redirect("custom_admin:admin_internships")

    return render(
        request,
        "custom_admin/edit_internship.html",
        {"internship": internship},
    )


@admin_required
def delete_internship(request, id):
    internship = get_object_or_404(Internship, id=id)
    internship.delete()
    return redirect("custom_admin:admin_internships")


@admin_required
def admin_job_applications(request):
    status_choices = [choice[0] for choice in JobApplication.STATUS_CHOICES]

    status_filter = request.GET.get("status", "All")
    search_query = request.GET.get("search", "").strip()
    job_filter = request.GET.get("job", "All")

    applications = JobApplication.objects.select_related("user", "job").all().order_by("-applied_at")

    if search_query:
        applications = applications.filter(
            Q(user__username__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )

    if status_filter != "All" and status_filter in status_choices:
        applications = applications.filter(status=status_filter)

    selected_job_id = None
    if job_filter != "All":
        try:
            selected_job_id = int(job_filter)
            applications = applications.filter(job_id=selected_job_id)
        except (TypeError, ValueError):
            selected_job_id = None

    if request.method == "POST":
        app_id = request.POST.get("app_id")
        new_status = request.POST.get("status")

        if new_status not in status_choices:
            messages.error(request, "Invalid status selected.")
            return redirect(request.get_full_path())

        application = get_object_or_404(JobApplication, id=app_id)
        application.status = new_status
        application.save(update_fields=["status"])

        messages.success(
            request,
            f"Job application status updated to '{new_status}' for {application.user.username}.",
        )
        return redirect(request.get_full_path())

    job_options = Job.objects.filter(id__in=applications.values_list("job_id", flat=True)).order_by("title")

    return render(
        request,
        "custom_admin/admin_job_applications.html",
        {
            "applications": applications,
            "status_choices": status_choices,
            "selected_status": status_filter,
            "search_query": search_query,
            "job_options": job_options,
            "selected_job_id": selected_job_id,
        },
    )


@admin_required
def admin_internship_applications(request):
    status_choices = [choice[0] for choice in InternshipApplication.STATUS_CHOICES]

    status_filter = request.GET.get("status", "All")
    search_query = request.GET.get("search", "").strip()
    internship_filter = request.GET.get("internship", "All")

    applications = InternshipApplication.objects.select_related("applicant", "internship").all().order_by("-applied_at")

    if search_query:
        applications = applications.filter(
            Q(applicant__username__icontains=search_query)
            | Q(applicant__first_name__icontains=search_query)
            | Q(applicant__last_name__icontains=search_query)
        )

    if status_filter != "All" and status_filter in status_choices:
        applications = applications.filter(status=status_filter)

    selected_internship_id = None
    if internship_filter != "All":
        try:
            selected_internship_id = int(internship_filter)
            applications = applications.filter(internship_id=selected_internship_id)
        except (TypeError, ValueError):
            selected_internship_id = None

    if request.method == "POST":
        app_id = request.POST.get("app_id")
        new_status = request.POST.get("status")

        if new_status not in status_choices:
            messages.error(request, "Invalid status selected.")
            return redirect(request.get_full_path())

        application = get_object_or_404(InternshipApplication, id=app_id)
        application.status = new_status
        application.save(update_fields=["status"])

        messages.success(
            request,
            f"Internship application status updated to '{new_status}' for {application.applicant.username}.",
        )
        return redirect(request.get_full_path())

    internship_options = Internship.objects.filter(
        id__in=applications.values_list("internship_id", flat=True)
    ).order_by("title")

    return render(
        request,
        "custom_admin/admin_internship_applications.html",
        {
            "applications": applications,
            "status_choices": status_choices,
            "selected_status": status_filter,
            "search_query": search_query,
            "internship_options": internship_options,
            "selected_internship_id": selected_internship_id,
        },
    )


def _candidate_display_name(user):
    full_name = (user.get_full_name() or "").strip()
    return full_name or user.username


def _normalize_interview_mode(mode_value):
    return "offline" if str(mode_value or "").strip().lower() == "offline" else "online"


def _backfill_interviews_from_job_applications():
    scheduled_apps = JobApplication.objects.select_related("user", "job").filter(
        status="Interview Scheduled"
    )

    for app in scheduled_apps:
        if not app.interview_date or not app.interview_time:
            continue

        mode = _normalize_interview_mode(app.interview_mode)
        defaults = {
            "candidate": app.user,
            "job": app.job,
            "interview_date": app.interview_date,
            "interview_time": app.interview_time,
            "mode": mode,
            "location": app.interview_location if mode == "offline" else None,
            "meeting_link": app.meeting_link if mode == "online" else None,
            "instructions": app.instructions,
            "status": "scheduled",
        }

        interview, created = InterviewSchedule.objects.get_or_create(
            application=app,
            defaults=defaults,
        )

        # Keep edited/cancelled/completed admin records intact.
        if not created and interview.status == "scheduled":
            for field_name, value in defaults.items():
                setattr(interview, field_name, value)
            interview.save()


def _sync_application_after_interview_change(interview, cancelled=False):
    application = interview.application
    application.interview_date = interview.interview_date if not cancelled else None
    application.interview_time = interview.interview_time if not cancelled else None
    application.interview_mode = interview.get_mode_display() if not cancelled else None
    application.meeting_link = interview.meeting_link if not cancelled else None
    application.interview_location = interview.location if not cancelled else None
    application.instructions = interview.instructions if not cancelled else None
    if cancelled and application.status == "Interview Scheduled":
        application.status = "Shortlisted"
    elif not cancelled:
        application.status = "Interview Scheduled"
    application.save()


@admin_required
def admin_interviews(request):
    try:
        try:
            _backfill_interviews_from_job_applications()
        except (OperationalError, ProgrammingError):
            pass

        interviews = InterviewSchedule.objects.select_related(
            "candidate",
            "job",
            "application",
        ).all().order_by("-interview_date", "-interview_time")

        if not interviews:
            fallback_apps = JobApplication.objects.select_related("user", "job").filter(
                status="Interview Scheduled"
            ).order_by("-interview_date", "-interview_time")
            interviews = [
                SimpleNamespace(
                    id=None,
                    candidate=app.user,
                    job=app.job,
                    interview_date=app.interview_date,
                    interview_time=app.interview_time,
                    mode=_normalize_interview_mode(app.interview_mode),
                    location=app.interview_location,
                    meeting_link=app.meeting_link,
                    status="scheduled",
                    is_fallback=True,
                )
                for app in fallback_apps
            ]
    except (OperationalError, ProgrammingError):
        interviews = []
        messages.error(request, "Interview management database is not ready. Please run migrations.")

    return render(
        request,
        "custom_admin/interviews.html",
        {"interviews": interviews},
    )


@admin_required
def edit_interview(request, id):
    try:
        interview = get_object_or_404(
            InterviewSchedule.objects.select_related("candidate", "job", "application"),
            id=id,
        )
    except (OperationalError, ProgrammingError):
        messages.error(request, "Interview management database is not ready. Please run migrations.")
        return redirect("custom_admin:admin_interviews")

    if request.method == "POST":
        date_str = (request.POST.get("date") or "").strip()
        time_str = (request.POST.get("time") or "").strip()
        mode = (request.POST.get("mode") or "").strip().lower()
        location = (request.POST.get("location") or "").strip()
        meeting_link = (request.POST.get("meeting_link") or "").strip()
        instructions = (request.POST.get("instructions") or "").strip()
        status = (request.POST.get("status") or interview.status).strip().lower()

        if not date_str or not time_str or mode not in {"online", "offline"}:
            messages.error(request, "Date, time, and valid mode are required.")
            return render(request, "custom_admin/edit_interview.html", {"interview": interview})

        if mode == "online" and not meeting_link:
            messages.error(request, "Meeting link is required for online interviews.")
            return render(request, "custom_admin/edit_interview.html", {"interview": interview})

        if mode == "offline" and not location:
            messages.error(request, "Location is required for offline interviews.")
            return render(request, "custom_admin/edit_interview.html", {"interview": interview})

        try:
            interview_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            interview_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            messages.error(request, "Please provide a valid date and time.")
            return render(request, "custom_admin/edit_interview.html", {"interview": interview})

        interview.interview_date = interview_date
        interview.interview_time = interview_time
        interview.mode = mode
        interview.location = location if mode == "offline" else None
        interview.meeting_link = meeting_link if mode == "online" else None
        interview.instructions = instructions or None
        interview.status = status if status in {"scheduled", "cancelled", "completed"} else "scheduled"
        interview.save()

        _sync_application_after_interview_change(
            interview,
            cancelled=(interview.status == "cancelled"),
        )

        contact_line = (
            f"Meeting Link: {interview.meeting_link}"
            if interview.mode == "online"
            else f"Location: {interview.location}"
        )

        if interview.candidate.email:
            try:
                send_mail(
                    subject="Updated Interview Schedule",
                    message=(
                        f"Dear {_candidate_display_name(interview.candidate)},\n\n"
                        "Your interview has been updated.\n\n"
                        "Interview Details:\n"
                        f"Date: {interview.interview_date}\n"
                        f"Time: {interview.interview_time}\n"
                        f"Mode: {interview.get_mode_display()}\n"
                        f"{contact_line}\n"
                        f"Instructions: {interview.instructions or 'No additional instructions.'}\n\n"
                        "Please check the updated details.\n\n"
                        "Regards,\n"
                        "CareerNest Hub Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[interview.candidate.email],
                )
                messages.success(request, "Interview updated and email sent.")
            except Exception:
                messages.warning(request, "Interview updated, but update email could not be sent.")
        else:
            messages.warning(request, "Interview updated, but candidate email is missing.")

        return redirect("custom_admin:admin_interviews")

    return render(request, "custom_admin/edit_interview.html", {"interview": interview})


@admin_required
def delete_interview(request, id):
    try:
        interview = get_object_or_404(InterviewSchedule.objects.select_related("application"), id=id)
    except (OperationalError, ProgrammingError):
        messages.error(request, "Interview management database is not ready. Please run migrations.")
        return redirect("custom_admin:admin_interviews")

    _sync_application_after_interview_change(interview, cancelled=True)
    interview.delete()
    messages.success(request, "Interview deleted successfully.")
    return redirect("custom_admin:admin_interviews")


@admin_required
def cancel_interview(request, id):
    try:
        interview = get_object_or_404(
            InterviewSchedule.objects.select_related("candidate", "job", "application"),
            id=id,
        )
    except (OperationalError, ProgrammingError):
        messages.error(request, "Interview management database is not ready. Please run migrations.")
        return redirect("custom_admin:admin_interviews")

    interview.status = "cancelled"
    interview.save(update_fields=["status", "updated_at"])
    _sync_application_after_interview_change(interview, cancelled=True)

    if interview.candidate.email:
        try:
            send_mail(
                subject="Correction: Interview Invitation Update",
                message=(
                    f"Dear {_candidate_display_name(interview.candidate)},\n\n"
                    f"We would like to inform you that the interview invitation previously sent to you for "
                    f"the position of {interview.job.title} was sent in error.\n\n"
                    "We sincerely apologize for any inconvenience caused.\n\n"
                    "Please ignore the previous interview details.\n\n"
                    "If you have any questions, feel free to contact us.\n\n"
                    "Best regards,\n"
                    "CareerNest Hub Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[interview.candidate.email],
            )
            messages.success(request, "Interview cancelled and apology email sent.")
        except Exception:
            messages.warning(request, "Interview cancelled, but apology email could not be sent.")
    else:
        messages.warning(request, "Interview cancelled, but candidate email is missing.")

    return redirect("custom_admin:admin_interviews")


@admin_required
def admin_recruiters(request):
    recruiters = _recruiter_queryset().order_by("-date_joined")
    return render(
        request,
        "custom_admin/admin_recruiters.html",
        {"recruiters": recruiters},
    )


@admin_required
def admin_contact_queries(request):
    queries = ContactQuery.objects.all().order_by("-created_at")
    return render(request, "admin_panel/contact_queries.html", {"queries": queries})


@admin_required
def reply_query(request, query_id):
    query = get_object_or_404(ContactQuery, id=query_id)

    if request.method == "POST":
        reply = (request.POST.get("reply") or "").strip()

        if not reply:
            messages.error(request, "Reply cannot be empty.")
            return render(request, "admin_panel/reply_query.html", {"query": query})

        query.admin_reply = reply
        query.is_resolved = True
        query.save(update_fields=["admin_reply", "is_resolved"])

        send_mail(
            "Response to your query",
            reply,
            settings.EMAIL_HOST_USER,
            [query.email],
            fail_silently=False,
        )

        messages.success(request, "Reply sent successfully.")
        return redirect("custom_admin:admin_contact_queries")

    return render(request, "admin_panel/reply_query.html", {"query": query})


@admin_required
def add_recruiter(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        company_name = request.POST.get("company_name", "").strip()

        if not username or not email or not password:
            messages.error(request, "Username, email and password are required.")
            return render(
                request,
                "custom_admin/add_recruiter.html",
                {
                    "form_data": {
                        "username": username,
                        "email": email,
                        "company_name": company_name,
                    }
                },
            )

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(
                request,
                "custom_admin/add_recruiter.html",
                {
                    "form_data": {
                        "username": username,
                        "email": email,
                        "company_name": company_name,
                    }
                },
            )

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(
                request,
                "custom_admin/add_recruiter.html",
                {
                    "form_data": {
                        "username": username,
                        "email": email,
                        "company_name": company_name,
                    }
                },
            )

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )
                user.is_staff = True
                user.save(update_fields=["is_staff"])
                _sync_recruiter_profile(user, company_name)
        except IntegrityError:
            messages.error(request, "Could not create recruiter account. Please try again.")
            return render(
                request,
                "custom_admin/add_recruiter.html",
                {
                    "form_data": {
                        "username": username,
                        "email": email,
                        "company_name": company_name,
                    }
                },
            )

        login_url = request.build_absolute_uri(reverse("login"))
        forgot_password_url = request.build_absolute_uri(reverse("forgot_password"))

        try:
            send_mail(
                subject="Your Recruiter Account Created",
                message=(
                    f"Hello {username},\n\n"
                    "Your recruiter account has been created.\n\n"
                    f"Username: {username}\n"
                    f"Email: {email}\n\n"
                    f"Password: {password}\n\n"
                    f"Login here: {login_url}\n"
                    f"Forgot password: {forgot_password_url}\n\n"
                    "Regards,\nCareerNest Hub"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "Recruiter created and login email sent successfully.")
        except Exception:
            messages.warning(
                request,
                "Recruiter created, but email sending failed. Please verify SMTP settings.",
            )

        return redirect("custom_admin:admin_recruiters")

    return render(request, "custom_admin/add_recruiter.html")


@admin_required
def edit_recruiter(request, id):
    user = get_object_or_404(_recruiter_queryset(), id=id)
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        company_name = request.POST.get("company_name", "").strip()

        if not username or not email:
            messages.error(request, "Username and email are required.")
            return render(
                request,
                "custom_admin/edit_recruiter.html",
                {"user_obj": user, "profile": profile},
            )

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Username already exists.")
            return render(
                request,
                "custom_admin/edit_recruiter.html",
                {"user_obj": user, "profile": profile},
            )

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email is already registered.")
            return render(
                request,
                "custom_admin/edit_recruiter.html",
                {"user_obj": user, "profile": profile},
            )

        user.username = username
        user.email = email
        user.is_staff = True
        if password:
            user.set_password(password)
        user.save()

        _sync_recruiter_profile(user, company_name)

        if password:
            login_url = request.build_absolute_uri(reverse("login"))
            try:
                send_mail(
                    subject="Your Recruiter Account Credentials Updated",
                    message=(
                        f"Hello {username},\n\n"
                        "Your recruiter account credentials were updated by admin.\n\n"
                        f"Username: {username}\n"
                        f"Password: {password}\n\n"
                        f"Login here: {login_url}\n\n"
                        "Regards,\nCareerNest Hub"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, "Recruiter updated and credential email sent.")
            except Exception:
                messages.warning(
                    request,
                    "Recruiter updated, but updated-credentials email could not be sent.",
                )
        else:
            messages.success(request, "Recruiter updated successfully.")
        return redirect("custom_admin:admin_recruiters")

    return render(
        request,
        "custom_admin/edit_recruiter.html",
        {"user_obj": user, "profile": profile},
    )


@admin_required
@require_POST
def delete_recruiter(request, id):
    user = get_object_or_404(_recruiter_queryset(), id=id)
    user.delete()
    messages.success(request, "Recruiter deleted successfully.")
    return redirect("custom_admin:admin_recruiters")
