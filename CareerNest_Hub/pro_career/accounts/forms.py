from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'full_name',
            'email',
            'role',
            'phone',
            'address',
            'company_name',
            'resume',
            'profile_image',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        base_classes = 'form-control'
        for name, field in self.fields.items():
            field.widget.attrs['class'] = base_classes

        if user and user.is_superuser:
            self.fields['role'].disabled = True
            self.fields['role'].help_text = 'Admin role is managed by system settings.'
            self.fields['role'].widget.attrs['data-locked'] = 'true'
