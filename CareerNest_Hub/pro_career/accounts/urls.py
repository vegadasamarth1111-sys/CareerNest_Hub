from django.urls import path
from . import views

urlpatterns = [
    path('', views.accounts_home, name='accounts_home'),

    # 🔐 AUTH
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # 🔥 FORGOT PASSWORD (NEW)
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
]