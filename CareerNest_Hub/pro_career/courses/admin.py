from django.contrib import admin
from .models import Course, Lecture


class LectureInline(admin.TabularInline):
    model = Lecture
    extra = 1


class CourseAdmin(admin.ModelAdmin):
    inlines = [LectureInline]


admin.site.register(Course, CourseAdmin)
admin.site.register(Lecture)