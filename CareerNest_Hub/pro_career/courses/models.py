from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User


# =========================
# COURSE MODEL
# =========================
class Course(models.Model):

    LEVEL_CHOICES = (
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
    )

    CATEGORY_CHOICES = (
        ("Programming", "Programming"),
        ("AI", "AI"),
        ("Web", "Web"),
        ("Data Science", "Data Science"),
        ("Design", "Design"),
        ("Business", "Business"),
    )

    LANGUAGE_CHOICES = (
        ("English", "English"),
        ("Hindi", "Hindi"),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True, unique=True)

    short_description = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    instructor = models.CharField(max_length=100, default="Admin", blank=True)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="Beginner", blank=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, blank=True, null=True)

    duration = models.CharField(max_length=50, default="4 weeks", blank=True)

    total_lectures = models.IntegerField(default=0, blank=True, null=True)

    price = models.IntegerField(default=0, blank=True, null=True)
    rating = models.FloatField(default=4.5, blank=True, null=True)

    students_enrolled = models.IntegerField(default=0, blank=True, null=True)

    certificate = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=True)

    image = models.ImageField(upload_to="course_images/", blank=True, null=True)

    preview_video = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # =========================
    # SAVE METHOD
    # =========================
    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.title)

        if self.preview_video:
            if "watch?v=" in self.preview_video:
                self.preview_video = self.preview_video.replace("watch?v=", "embed/")
            elif "youtu.be/" in self.preview_video:
                video_id = self.preview_video.split("/")[-1]
                self.preview_video = f"https://www.youtube.com/embed/{video_id}"

        super().save(*args, **kwargs)

    def update_total_lectures(self):
        self.total_lectures = self.lectures.count()
        super().save(update_fields=["total_lectures"])

    def __str__(self):
        return self.title


# =========================
# ENROLLMENT MODEL 🔥 (NEW)
# =========================
class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    is_paid = models.BooleanField(default=False)

    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)

    enrolled_at = models.DateTimeField(default=timezone.now)

    # 🔥 Prevent duplicate enrollment
    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} → {self.course.title}"


# =========================
# LECTURE MODEL
# =========================
class Lecture(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lectures"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video = models.FileField(
        upload_to="course_videos/",
        blank=True,
        null=True
    )

    video_url = models.URLField(blank=True, null=True)

    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # =========================
    # SAVE METHOD
    # =========================
    def save(self, *args, **kwargs):

        if self.video_url:
            if "watch?v=" in self.video_url:
                self.video_url = self.video_url.replace("watch?v=", "embed/")
            elif "youtu.be/" in self.video_url:
                video_id = self.video_url.split("/")[-1]
                self.video_url = f"https://www.youtube.com/embed/{video_id}"

        super().save(*args, **kwargs)

        # update lecture count
        self.course.update_total_lectures()

    def delete(self, *args, **kwargs):
        course = self.course
        super().delete(*args, **kwargs)
        course.update_total_lectures()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["order"]
