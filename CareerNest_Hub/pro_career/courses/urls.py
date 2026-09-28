from django.urls import path
from . import views

# 🔥 Namespace (IMPORTANT)
app_name = 'courses'

urlpatterns = [

    # ==============================
    # COURSE LIST
    # ==============================
    path('', views.course_list, name='course_list'),

    # ==============================
    # ENROLL + PAYMENT (NEW 🔥)
    # ==============================
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('payment-success/', views.payment_success, name='payment_success'),

    # ==============================
    # ADMIN: ADD COURSE
    # ==============================
    path('add/', views.add_course, name='add_course'),

    # ==============================
    # ADMIN: EDIT COURSE
    # ==============================
    path('edit/<int:id>/', views.edit_course, name='edit_course'),

    # ==============================
    # ADMIN: DELETE COURSE
    # ==============================
    path('delete/<int:id>/', views.delete_course, name='delete_course'),
]