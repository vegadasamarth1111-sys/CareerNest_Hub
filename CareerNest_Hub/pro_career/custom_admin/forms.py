from django import forms

from courses.models import Course, Lecture
from internships.models import Internship
from jobs.models import Job


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = "__all__"
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "created_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.fields.get("created_at") and self.instance and self.instance.pk and self.instance.created_at:
            self.initial["created_at"] = self.instance.created_at.strftime("%Y-%m-%dT%H:%M")

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs["class"] = "form-control premium-input"
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs["class"] = "form-select premium-input"
            else:
                field.widget.attrs["class"] = "form-control premium-input"


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "requirements" in self.fields:
            self.fields["requirements"].widget = forms.Textarea(attrs={"rows": 3})

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs["class"] = "form-select premium-input"
            else:
                field.widget.attrs["class"] = "form-control premium-input"


class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "skills_required" in self.fields:
            self.fields["skills_required"].widget = forms.Textarea(attrs={"rows": 3})

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs["class"] = "form-select premium-input"
            else:
                field.widget.attrs["class"] = "form-control premium-input"


class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "course" in self.fields:
            self.fields["course"].required = False
            self.fields["course"].widget = forms.HiddenInput()

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.HiddenInput):
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs["class"] = "form-select premium-input"
            else:
                field.widget.attrs["class"] = "form-control premium-input"

    def clean(self):
        cleaned_data = super().clean()
        video = cleaned_data.get("video")
        video_url = cleaned_data.get("video_url")

        if not video and not video_url:
            raise forms.ValidationError("Please upload a video file or provide a video URL.")

        return cleaned_data
