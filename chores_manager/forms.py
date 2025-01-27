from django import forms
from django.contrib.auth.models import User

class CustomUserCreationForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15, required=True, label="Phone Number")
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    opt_in_sms = forms.BooleanField(required=True, label="Receive SMS messages",
        help_text="<br>I agree to the <a href='/terms/' target='_blank'>Terms of Service</a>, "
                "<a href='/privacy/' target='_blank'>Privacy Policy</a> "
                "and <a href='/data-deletion/' target='_blank'>Data Deletion Policy</a>, "
                "including receiving SMS messages about weekly chores from Phi Delt Chores Manager. "
                "Message frequency may vary. Message and data rates may apply. "
                "Reply HELP for help and STOP to opt-out.")

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'opt_in_sms']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "<br>You may use letters, digits, and @/./+/-/_ characters."

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        # Save the additional fields like phone number and opt-in preference here
        if hasattr(user, 'profile'):
            user.profile.phone_number = self.cleaned_data["phone_number"]
            user.profile.opt_in_sms = self.cleaned_data["opt_in_sms"]
            user.profile.save()
        return user

