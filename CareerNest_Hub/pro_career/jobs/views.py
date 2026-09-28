from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from datetime import datetime

from .models import Job, JobApplication, InterviewSchedule

# internship import
from internships.models import InternshipApplication


def _is_student_user(user):
    if not user.is_authenticated or user.is_superuser:
        return False

    profile = getattr(user, "profile", None)
    if not profile:
        return True

    return profile.role == "student"



# =====================================
# Admin / Staff: View applicants for job
# =====================================

@staff_member_required
def job_applicants(request, job_id):

    job = get_object_or_404(Job, id=job_id)

    applications = JobApplication.objects.filter(
        job=job
    )

    return render(
        request,
        'jobs/job_applicants.html',
        {
            'job': job,
            'applications': applications
        }
    )



# =====================================
# Recruiter Panel
# =====================================

@login_required
def recruiter_applications(request):
    profile = getattr(request.user, "profile", None)
    is_recruiter = bool(profile and profile.role == "recruiter")
    has_job_permission = request.user.has_perm("jobs.change_jobapplication")

    if not (request.user.is_superuser or has_job_permission or is_recruiter):
        messages.error(request, "Recruiter access only.")
        return redirect("dashboard_home")

    status_filter = request.GET.get("status")
    search_query = request.GET.get("search")
    job_filter = request.GET.get("job")

    applications = JobApplication.objects.select_related(
        "user",
        "job"
    )

    recruiter_company = getattr(profile, "company_name", None) if is_recruiter else None
    if is_recruiter and not (request.user.is_superuser or has_job_permission):
        if recruiter_company:
            applications = applications.filter(job__company=recruiter_company)
        else:
            applications = applications.none()

    job_options = Job.objects.filter(
        id__in=applications.values_list("job_id", flat=True)
    ).order_by("title")

    # 🔎 Search filter
    if search_query:

        applications = applications.filter(
            Q(user__username__icontains=search_query)
        )

    # 🎯 Status filter
    if status_filter and status_filter != "All":

        applications = applications.filter(
            status=status_filter
        )

    selected_job_id = None
    if job_filter and job_filter != "All":
        try:
            selected_job_id = int(job_filter)
            applications = applications.filter(job_id=selected_job_id)
        except (TypeError, ValueError):
            selected_job_id = None

    # 🎯 Update status
    if request.method == "POST":

        app_id = request.POST.get("app_id")
        status = request.POST.get("status")

        application = get_object_or_404(
            JobApplication,
            id=app_id
        )

        if is_recruiter and not (request.user.is_superuser or has_job_permission):
            if not recruiter_company or application.job.company != recruiter_company:
                messages.error(request, "You are not authorized to update this application.")
                return redirect("recruiter_applications")

        if status == "Interview Scheduled":
            return redirect("schedule_interview", id=application.id)

        application.status = status
        application.save()

        messages.success(
            request,
            f"Status updated to '{status}' for {application.user.username}"
        )

        return redirect(
            "recruiter_applications"
        )

    return render(
        request,
        "jobs/recruiter_applications.html",
        {
            "applications": applications,
            "selected_status": status_filter or "All",
            "search_query": search_query or "",
            "job_options": job_options,
            "selected_job_id": selected_job_id,
        }
    )


@login_required
def schedule_interview(request, id):
    profile = getattr(request.user, "profile", None)
    is_recruiter = bool(profile and profile.role == "recruiter")
    has_job_permission = request.user.has_perm("jobs.change_jobapplication")

    if not (request.user.is_superuser or has_job_permission or is_recruiter):
        messages.error(request, "Recruiter access only.")
        return redirect("dashboard_home")

    application = get_object_or_404(
        JobApplication.objects.select_related("user", "job"),
        id=id
    )

    recruiter_company = getattr(profile, "company_name", None) if is_recruiter else None
    if is_recruiter and not (request.user.is_superuser or has_job_permission):
        if not recruiter_company or application.job.company != recruiter_company:
            messages.error(request, "You are not authorized to schedule this interview.")
            return redirect("recruiter_applications")

    if request.method == "POST":
        date_str = (request.POST.get("date") or "").strip()
        time_str = (request.POST.get("time") or "").strip()
        interview_mode = (request.POST.get("mode") or "").strip()
        meeting_link = (request.POST.get("link") or "").strip()
        interview_location = (request.POST.get("location") or "").strip()
        instructions = (request.POST.get("instructions") or "").strip()
        mode_lower = interview_mode.lower()

        if not date_str or not time_str or not interview_mode:
            messages.error(request, "Date, time, and interview mode are required.")
        elif mode_lower == "online" and not meeting_link:
            messages.error(request, "Meeting link is required for online interviews.")
        elif mode_lower == "offline" and not interview_location:
            messages.error(request, "Interview location is required for offline interviews.")
        else:
            try:
                interview_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                interview_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                messages.error(request, "Please enter a valid date and time.")
            else:
                application.status = "Interview Scheduled"
                application.interview_date = interview_date
                application.interview_time = interview_time
                application.interview_mode = interview_mode
                application.meeting_link = meeting_link or None if mode_lower == "online" else None
                application.interview_location = interview_location or None if mode_lower == "offline" else None
                application.instructions = instructions or None
                application.save()

                try:
                    InterviewSchedule.objects.update_or_create(
                        application=application,
                        defaults={
                            "candidate": application.user,
                            "job": application.job,
                            "interview_date": interview_date,
                            "interview_time": interview_time,
                            "mode": mode_lower if mode_lower in {"online", "offline"} else "online",
                            "location": application.interview_location,
                            "meeting_link": application.meeting_link,
                            "instructions": application.instructions,
                            "status": "scheduled",
                        },
                    )
                except (OperationalError, ProgrammingError):
                    messages.warning(
                        request,
                        "Interview saved, but interview management sync is pending migrations."
                    )

                interview_detail_line = "Meeting Link: N/A"
                if mode_lower == "online":
                    interview_detail_line = f"Meeting Link: {application.meeting_link}"
                elif mode_lower == "offline":
                    interview_detail_line = f"Interview Location: {application.interview_location}"

                email_sent = False
                if application.user.email:
                    try:
                        send_mail(
                            subject="Interview Scheduled - CareerNest Hub",
                            message=(
                                f"Dear {application.user.username},\n\n"
                                "Your interview has been scheduled successfully.\n\n"
                                f"Job Role: {application.job.title}\n\n"
                                "Interview Details:\n"
                                f"- Date: {application.interview_date}\n"
                                f"- Time: {application.interview_time}\n"
                                f"- Mode: {application.interview_mode}\n"
                                f"- {interview_detail_line}\n\n"
                                "Instructions:\n"
                                f"{application.instructions or 'No additional instructions.'}\n\n"
                                "Please join on time and be prepared.\n\n"
                                "Best of luck!\n\n"
                                "CareerNest Team"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[application.user.email],
                        )
                        email_sent = True
                    except Exception:
                        messages.warning(
                            request,
                            "Interview saved, but email could not be sent right now."
                        )
                else:
                    messages.warning(
                        request,
                        "Interview saved, but candidate email is missing."
                    )

                if email_sent:
                    messages.success(request, "Interview scheduled and email sent successfully.")
                elif not application.user.email:
                    messages.success(request, "Interview scheduled successfully.")

                return redirect("schedule_interview", id=application.id)

    applications = JobApplication.objects.select_related("user", "job").filter(
        status="Interview Scheduled"
    ).order_by("-interview_date", "-interview_time")

    if is_recruiter and not (request.user.is_superuser or has_job_permission):
        if recruiter_company:
            applications = applications.filter(job__company=recruiter_company)
        else:
            applications = applications.none()

    return render(
        request,
        "jobs/schedule_interview.html",
        {
            "application": application,
            "applications": applications,
        }
    )



# =====================================
# Show all jobs
# =====================================

@login_required
def jobs_list(request):

    jobs = Job.objects.all()

    return render(
        request,
        "jobs/jobs_list.html",
        {
            "jobs": jobs
        }
    )



# =====================================
# Job detail
# =====================================

@login_required
def job_detail(request, id):

    job = get_object_or_404(
        Job,
        id=id
    )

    already_applied = False

    if request.user.is_authenticated:

        already_applied = JobApplication.objects.filter(
            user=request.user,
            job=job
        ).exists()

    return render(
        request,
        "jobs/job_detail.html",
        {
            "job": job,
            "already_applied": already_applied
        }
    )



# =====================================
# Apply job
# =====================================

@login_required
def apply_job(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id
    )

    if job.is_expired():
        messages.error(request, "This job posting has expired.")
        return redirect("job_detail", id=job.id)

    if request.method == "POST":

        resume = request.FILES.get("resume")

        already_applied = JobApplication.objects.filter(
            user=request.user,
            job=job
        ).exists()

        if not already_applied:

            JobApplication.objects.create(
                user=request.user,
                job=job,
                resume=resume
            )

        return redirect(
            "my_applications"
        )

    return render(
        request,
        "jobs/apply_job.html",
        {
            "job": job
        }
    )



# =====================================
# My Applications (Jobs + Internships)
# =====================================

@login_required
def my_applications(request):
    if not _is_student_user(request.user):
        return HttpResponseForbidden("Only students can access My Applications.")

    job_apps = JobApplication.objects.filter(
        user=request.user
    ).select_related("job")

    internship_apps = InternshipApplication.objects.filter(
        applicant=request.user
    ).select_related("internship")

    return render(
        request,
        "applications/my_applications.html",
        {
            "job_apps": job_apps,
            "internship_apps": internship_apps,
        }
    )



# =====================================
# Revoke job application
# =====================================

@login_required
def revoke_application(request, app_id):
    if not _is_student_user(request.user):
        return HttpResponseForbidden("Only students can revoke applications.")

    app = get_object_or_404(
        JobApplication,
        id=app_id,
        user=request.user
    )

    if app.status == "Applied":
        app.delete()

    return redirect(
        "my_applications"
    )


@login_required
def withdraw_application(request, app_id):
    return revoke_application(request, app_id)
