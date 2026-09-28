from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Home view
from dashboard.views import contact_success, contact_view, home
from accounts.views import (
    CustomPasswordChangeDoneView,
    CustomPasswordChangeView,
    delete_profile,
    profile_view,
)

urlpatterns = [

    # =========================
    # HOME
    # =========================
    path('', home, name='home'),
    path('contact/', contact_view, name='contact'),
    path('contact/success/', contact_success, name='contact_success'),
    path('profile/', profile_view, name='profile'),
    path('profile/delete/', delete_profile, name='delete_profile'),
    path('profile/change-password/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('profile/change-password/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),

    # =========================
    # DJANGO ADMIN (DEFAULT)
    # =========================
    path('admin/', admin.site.urls),

    # =========================
    # APPS
    # =========================
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('internships/', include('internships.urls')),

    #  IMPORTANT (NAMESPACE SAFE)
    path('courses/', include(('courses.urls', 'courses'), namespace='courses')),

    path('mycourses/', include('mycourses.urls')),

    #  CUSTOM ADMIN PANEL
    path('admin-panel/', include(('custom_admin.urls', 'custom_admin'), namespace='custom_admin')),

    path('chat/', include('chat.urls')),
]


import os
from django.http import HttpResponse
from django.core.management import call_command
from jobs.models import Job
from internships.models import Internship
from courses.models import Course

def seed_now(request):
    results = ["<h2>Database Seeder & Diagnostics</h2>"]
    results.append(f"<b>Database Engine:</b> {settings.DATABASES['default']['ENGINE']}")
    results.append(f"<b>Jobs count:</b> {Job.objects.count()}")
    results.append(f"<b>Internships count:</b> {Internship.objects.count()}")
    results.append(f"<b>Courses count:</b> {Course.objects.count()}")
    
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'datadump.json'),
        os.path.join(settings.BASE_DIR.parent, 'datadump.json'),
        os.path.join(settings.BASE_DIR, 'CareerNest_Hub', 'pro_career', 'datadump.json'),
        'datadump.json'
    ]
    dump_path = None
    for p in possible_paths:
        if os.path.exists(p):
            dump_path = p
            break
            
    if not dump_path:
        results.append(f"<p style='color:red;'><b>ERROR:</b> datadump.json not found in checked paths.</p>")
    else:
        results.append(f"<p style='color:blue;'>Found datadump.json at: <code>{dump_path}</code></p>")
        try:
            call_command('loaddata', dump_path)
            results.append("<p style='color:green;'><b>SUCCESS:</b> Data loaded cleanly into database!</p>")
        except Exception as e:
            results.append(f"<p style='color:red;'><b>Load notice:</b> {str(e)}</p>")
            
    results.append(f"<hr><b>Updated Jobs count:</b> {Job.objects.count()}")
    results.append(f"<br><b>Updated Internships count:</b> {Internship.objects.count()}")
    results.append(f"<br><b>Updated Courses count:</b> {Course.objects.count()}")
    results.append("<br><br><a href='/jobs/' style='font-size:18px; color:green; font-weight:bold;'>👉 Click here to go to Jobs Page</a>")
    
    return HttpResponse("<br>".join(results), content_type="text/html")

from django.urls import re_path
from django.views.static import serve

urlpatterns += [
    path('seed-now/', seed_now, name='seed_now'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
