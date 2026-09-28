from django.db import models
from django.contrib.auth.models import User
from courses.models import Course, Lecture


# =========================
# ENROLLED COURSE MODEL
# =========================
class MyCourse(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="my_courses"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrolled_students"
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True
    )

    is_paid = models.BooleanField(
        default=False
    )

    progress = models.IntegerField(
        default=0
    )

    completed = models.BooleanField(
        default=False
    )

    certificate_issued = models.BooleanField(
        default=False
    )

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"


# =========================
# COMPLETED LECTURES MODEL 🔥
# =========================
class CompletedLecture(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE
    )

    completed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("user", "lecture")

    def __str__(self):
        return f"{self.user.username} completed {self.lecture.title}"