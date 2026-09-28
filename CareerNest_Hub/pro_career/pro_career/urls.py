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


# =========================
# MEDIA FILES 
# =========================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
