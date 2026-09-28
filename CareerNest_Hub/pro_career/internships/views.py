from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden

from .models import Internship, InternshipApplication


def _is_student_user(user):
    if not user.is_authenticated or user.is_superuser:
        return False

    profile = getattr(user, "profile", None)
    if not profile:
        return True

    return profile.role == "student"


# =====================================
# Show all internships
# =====================================

def internship_list(request):
    internships = Internship.objects.all()

    return render(
        request,
        "internships/internship_list.html",
        {
            "internships": internships
        }
    )


# =====================================
# Internship detail
# =====================================

def internship_detail(request, id):
    internship = get_object_or_404(Internship, id=id)

    already_applied = False
    if request.user.is_authenticated:
        already_applied = InternshipApplication.objects.filter(
            internship=internship,
            applicant=request.user
        ).exists()

    return render(
        request,
        "internships/internship_detail.html",
        {
            "internship": internship,
            "already_applied": already_applied,
        }
    )


# =====================================
# Apply internship
# =====================================

@login_required
def apply_internship(request, internship_id):

    internship = get_object_or_404(Internship, id=internship_id)

    if internship.is_expired():
        messages.error(request, "This internship posting has expired.")
        return redirect("internships:internship_list")

    if request.method == "POST":

        resume = request.FILES.get("resume")

        already_applied = InternshipApplication.objects.filter(
            internship=internship,
            applicant=request.user
        ).first()

        if already_applied:
            messages.warning(request, "You already applied for this internship")
            return redirect("/jobs/my-applications/")

        InternshipApplication.objects.create(
            internship=internship,
            applicant=request.user,
            resume=resume,
            status="Applied"
        )

        messages.success(request, "Internship application submitted successfully")

        return redirect("/jobs/my-applications/")

    return render(
        request,
        "internships/apply_internship.html",
        {
            "internship": internship
        }
    )


# =====================================
# RECRUITER PANEL
# =====================================

@login_required
def recruiter_internship_applications(request):

    profile = getattr(request.user, "profile", None)

    # Only recruiter allowed
    if not profile or profile.role != "recruiter":
        return HttpResponseForbidden("You are not authorized")

    company = profile.company_name

    status_filter = request.GET.get("status")
    search_query = request.GET.get("search")

    applications = InternshipApplication.objects.select_related(
        "applicant",
        "internship"
    ).filter(
        internship__company=company
    )

    # Search
    if search_query:
        applications = applications.filter(
            Q(applicant__username__icontains=search_query)
        )

    # Status filter
    if status_filter and status_filter != "All":
        applications = applications.filter(status=status_filter)

    # Update status
    if request.method == "POST":

        app_id = request.POST.get("app_id")
        status = request.POST.get("status")

        application = get_object_or_404(
            InternshipApplication,
            id=app_id,
            internship__company=company
        )

        application.status = status
        application.save()

        messages.success(
            request,
            f"Status updated to '{status}' for {application.applicant.username}"
        )

        return redirect("internships:recruiter_internship_applications")

    return render(
        request,
        "internships/recruiter_applications.html",
        {
            "applications": applications,
            "selected_status": status_filter or "All",
            "search_query": search_query or "",
        }
    )


# =====================================
# Revoke internship
# =====================================

@login_required
def revoke_internship(request, app_id):
    if not _is_student_user(request.user):
        return HttpResponseForbidden("Only students can revoke internship applications.")

    application = get_object_or_404(
        InternshipApplication,
        id=app_id,
        applicant=request.user
    )

    if application.status == "Applied":
        application.delete()
        messages.warning(request, "Internship application revoked")
    else:
        messages.error(request, "Cannot revoke this application")

    return redirect("/jobs/my-applications/")
