import random
import time

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .forms import ProfileForm
from .models import Profile


def _post_login_redirect(user):
    if user.is_superuser:
        return 'custom_admin:admin_dashboard'

    if hasattr(user, 'profile') and user.profile.role == 'recruiter':
        return 'recruiter_applications'

    return 'dashboard_home'


def _base_template_for_user(user):
    return 'admin_panel/base.html' if user.is_superuser else 'dashboard/base.html'


def _profile_role_label(user, profile):
    if user.is_superuser:
        return 'Admin'
    if profile and profile.role:
        return profile.get_role_display()
    return 'Student'


# ==============================
# HOME
# ==============================
def accounts_home(request):
    return render(request, 'accounts/home.html')


# ==============================
# LOGIN VIEW
# ==============================
def login_view(request):

    if request.user.is_authenticated:
        return redirect(_post_login_redirect(request.user))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:

            if user.is_superuser:
                return render(request, 'accounts/login.html', {
                    'error': 'Admin must login from admin panel'
                })

            login(request, user)
            return redirect(_post_login_redirect(user))

        return render(request, 'accounts/login.html', {
            'error': 'Invalid credentials'
        })

    return render(request, 'accounts/login.html')


# ==============================
# REGISTER
# ==============================
def register_view(request):

    if request.user.is_authenticated:
        return redirect(_post_login_redirect(request.user))

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/register.html', {
                'error': 'Username already exists'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'accounts/register.html', {
                'error': 'Email already registered'
            })

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(request, 'Account created successfully')
        return redirect('login')

    return render(request, 'accounts/register.html')


# ==============================
# LOGOUT
# ==============================
def logout_view(request):
    logout(request)
    return redirect('login')


# ==============================
# PROFILE (VIEW + EDIT)
# ==============================
@login_required
def profile_view(request):
    default_role = 'admin' if request.user.is_superuser else 'student'
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
            'role': default_role,
        },
    )

    if request.user.is_superuser and profile.role != 'admin':
        profile.role = 'admin'
        profile.save(update_fields=['role'])

    needs_profile_sync = False
    if not profile.email and request.user.email:
        profile.email = request.user.email
        needs_profile_sync = True
    if not profile.full_name and request.user.get_full_name():
        profile.full_name = request.user.get_full_name()
        needs_profile_sync = True
    if needs_profile_sync:
        profile.save(update_fields=['email', 'full_name'])

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            updated_profile = form.save(commit=False)
            updated_profile.user = request.user
            if request.user.is_superuser:
                updated_profile.role = 'admin'
            updated_profile.save()

            if updated_profile.email != request.user.email:
                request.user.email = updated_profile.email
                request.user.save(update_fields=['email'])

            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile_obj': profile,
        'base_template': _base_template_for_user(request.user),
        'role_label': _profile_role_label(request.user, profile),
        'has_form_errors': bool(form.errors),
    })


# ==============================
# DELETE PROFILE
# ==============================
@login_required
@require_POST
def delete_profile(request):
    profile = getattr(request.user, 'profile', None)
    if profile:
        profile.delete()

    Profile.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': '',
            'email': request.user.email,
            'role': 'admin' if request.user.is_superuser else 'student',
        },
    )

    messages.success(request, 'Profile details deleted and reset.')
    return redirect('home')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change_form.html'
    success_url = reverse_lazy('password_change_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = _base_template_for_user(self.request.user)
        return context


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = _base_template_for_user(self.request.user)
        return context


# =====================================================
# FORGOT PASSWORD (SEND OTP)
# =====================================================
def forgot_password(request):

    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            User.objects.get(email=email)

            otp = str(random.randint(100000, 999999))

            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            request.session['otp_time'] = time.time()

            send_mail(
                subject='CareerNest Password Reset OTP',
                message=f'Your OTP is: {otp}',
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request, 'OTP sent to your email')
            return redirect('verify_otp')

        except User.DoesNotExist:
            messages.error(request, 'Email not registered')

    return render(request, 'accounts/forgot_password.html')


# =====================================================
# VERIFY OTP + RESET PASSWORD
# =====================================================
def verify_otp(request):

    email = request.session.get('reset_email')
    session_otp = request.session.get('reset_otp')
    otp_time = request.session.get('otp_time')

    if not email or not session_otp or not otp_time:
        messages.error(request, 'Session expired. Try again.')
        return redirect('forgot_password')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if time.time() - otp_time > 300:
            messages.error(request, 'OTP expired')
            return redirect('forgot_password')

        if entered_otp != session_otp:
            messages.error(request, 'Invalid OTP')
            return redirect('verify_otp')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('verify_otp')

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            request.session.flush()

            messages.success(request, 'Password updated successfully')
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, 'Something went wrong')
            return redirect('forgot_password')

    return render(request, 'accounts/verify_otp.html')


# =====================================================
# RESEND OTP
# =====================================================
def resend_otp(request):

    email = request.session.get('reset_email')

    if not email:
        messages.error(request, 'Session expired')
        return redirect('forgot_password')

    otp = str(random.randint(100000, 999999))

    request.session['reset_otp'] = otp
    request.session['otp_time'] = time.time()

    send_mail(
        subject='CareerNest New OTP',
        message=f'Your new OTP is: {otp}',
        from_email=None,
        recipient_list=[email],
        fail_silently=False,
    )

    messages.success(request, 'New OTP sent')
    return redirect('verify_otp')
