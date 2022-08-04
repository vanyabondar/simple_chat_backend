from django import forms
from django.core.exceptions import ValidationError
from .models import Thread


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['participants',]

    def clean(self):
        """
        Checks that thread has exactly 2 participants
        """
        participants = self.cleaned_data.get('participants')
        if participants is None or len(participants) != 2:
            raise ValidationError('Each thread must include exactly 2 participants')
        return self.cleaned_data
