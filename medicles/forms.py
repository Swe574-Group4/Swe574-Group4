from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import fields

class TagForm(forms.Form):
    tag_key = forms.CharField(label='Tag Key', max_length=300, required=False)
    user_def_tag_key = forms.CharField(label='User Tag Value', max_length=300, required=False)
    
class SingupForm(UserCreationForm):
    email = forms.EmailField(max_length=100, help_text="Please provide valid email address.")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)
