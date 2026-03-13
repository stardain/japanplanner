from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Your Unique Name"
        self.fields['password1'].label = "Create a Strong Password"

        # 2. Optional: Add the AJAX URL directly to the input
        self.fields['username'].widget.attrs.update({
            'data-validate-url': '/ajax/validate-username/'
        })