from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import razorpay

from .models import Course, Enrollment
from mycourses.models import MyCourse


# =========================================
# COURSE LIST (FOR ALL USERS)
# =========================================
@login_required
def course_list(request):
    courses = Course.objects.all()

    # Get enrolled courses for current user
    enrolled_courses = Enrollment.objects.filter(
        user=request.user,
        is_paid=True  # only paid courses
    ).values_list('course_id', flat=True)

    return render(
        request,
        "courses/course_list.html",
        {
            "courses": courses,
            "enrolled_courses": enrolled_courses
        }
    )


# =========================================
# ENROLL COURSE (RAZORPAY PAYMENT)
# =========================================
@login_required
def enroll_course(request, course_id):

    course = get_object_or_404(Course, id=course_id)

    # Prevent duplicate paid enrollment
    if Enrollment.objects.filter(
        user=request.user,
        course=course,
        is_paid=True
    ).exists():
        return redirect('my_courses')

    # Razorpay client
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    amount = int(course.price) * 100  # paisa

    # Create order
    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    # Create or update pending enrollment
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={
            "is_paid": False,
            "razorpay_order_id": payment['id']
        }
    )

    if not created:
        enrollment.razorpay_order_id = payment['id']
        enrollment.save(update_fields=["razorpay_order_id"])

    return render(request, "courses/payment.html", {
        "course": course,
        "payment": payment,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": payment["amount"],
        "order_id": payment["id"],
    })


# =========================================
# PAYMENT SUCCESS (VERIFY)
# =========================================
@csrf_exempt
@login_required
def payment_success(request):

    if request.method == "POST":

        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            # VERIFY PAYMENT (CRITICAL)
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Update enrollment (NOT create)
            enrollment = Enrollment.objects.get(
                razorpay_order_id=razorpay_order_id
            )

            if not enrollment.is_paid:
                enrollment.is_paid = True
                enrollment.razorpay_payment_id = razorpay_payment_id
                enrollment.save(update_fields=["is_paid", "razorpay_payment_id"])

                # Ensure paid users can access course content immediately.
                MyCourse.objects.get_or_create(
                    user=enrollment.user,
                    course=enrollment.course,
                    defaults={"is_paid": True}
                )

                # Increase enrolled count safely
                course = enrollment.course
                course.students_enrolled = (course.students_enrolled or 0) + 1
                course.save(update_fields=["students_enrolled"])
            else:
                my_course, _ = MyCourse.objects.get_or_create(
                    user=enrollment.user,
                    course=enrollment.course
                )
                if not my_course.is_paid:
                    my_course.is_paid = True
                    my_course.save(update_fields=["is_paid"])

            return redirect('my_courses')

        except Exception as e:
            print("Payment verification failed:", e)
            return redirect('courses:course_list')

    return redirect('courses:course_list')


# =========================================
# ADD COURSE (ADMIN ONLY)
# =========================================
@login_required
def add_course(request):

    if not request.user.is_superuser:
        return redirect('courses:course_list')

    if request.method == "POST":
        title = request.POST.get('title')
        price = request.POST.get('price')

        if title and price:
            Course.objects.create(title=title, price=price)

        return redirect('courses:course_list')

    return render(request, 'courses/add_course.html')


# =========================================
# EDIT COURSE (ADMIN ONLY)
# =========================================
@login_required
def edit_course(request, id):

    if not request.user.is_superuser:
        return redirect('courses:course_list')

    course = get_object_or_404(Course, id=id)

    if request.method == "POST":
        title = request.POST.get('title')
        price = request.POST.get('price')

        if title and price:
            course.title = title
            course.price = price
            course.save()

        return redirect('courses:course_list')

    return render(request, 'courses/edit_course.html', {
        'course': course
    })


# =========================================
# DELETE COURSE (ADMIN ONLY)
# =========================================
@login_required
def delete_course(request, id):

    if not request.user.is_superuser:
        return redirect('courses:course_list')

    course = get_object_or_404(Course, id=id)
    course.delete()

    return redirect('courses:course_list')
