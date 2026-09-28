from django import forms

from .models import ContactQuery


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactQuery
        fields = ["name", "email", "subject", "message"]
