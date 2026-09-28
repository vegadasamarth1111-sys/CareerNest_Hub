from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import OperationalError, ProgrammingError

from jobs.models import JobApplication
from internships.models import InternshipApplication

from .forms import ContactForm


def _recruiter_dashboard_context(user):
    context = {
        "applied": 0,
        "total_jobs": 0,
        "total_internships": 0,
        "shortlisted": 0,
        "interviews": 0,
        "recent_applications": [],
    }

    role = ""
    if user.is_authenticated:
        try:
            role = user.profile.role
        except ObjectDoesNotExist:
            role = ""

    if role == "recruiter":
        try:
            context["applied"] = JobApplication.objects.filter(status__iexact="applied").count()
            context["total_jobs"] = JobApplication.objects.count()
            context["total_internships"] = InternshipApplication.objects.count()
            context["shortlisted"] = JobApplication.objects.filter(status__iexact="shortlisted").count()
            context["interviews"] = JobApplication.objects.filter(status__iexact="interview scheduled").count()
            context["recent_applications"] = JobApplication.objects.order_by("-applied_date")[:5]
        except (OperationalError, ProgrammingError):
            # Keeps dashboard usable if schema is temporarily out of sync.
            pass

    return context


# ==============================
# STUDENT DASHBOARD
# ==============================
@login_required
def dashboard_home(request):

    # BLOCK ADMIN FROM STUDENT DASHBOARD
    if request.user.is_superuser:
        return redirect("admin_dashboard")

    return render(request, "dashboard/home.html", _recruiter_dashboard_context(request.user))


# ==============================
# HOME PAGE
# ==============================
def home(request):
    return render(request, "dashboard/home.html", _recruiter_dashboard_context(request.user))


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            query = form.save()

            send_mail(
                "We received your query",
                "Thank you for contacting us. Our admin will reply soon.",
                settings.EMAIL_HOST_USER,
                [query.email],
                fail_silently=False,
            )

            return redirect("contact_success")
    else:
        form = ContactForm()

    return render(request, "contact/contact.html", {"form": form})


def contact_success(request):
    return render(request, "contact/contact_success.html")
