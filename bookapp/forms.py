from django import forms

from .models import SpecialCategory, MainCategory, UnderCategory, Book, Cart, UserAccount


class UserAccountForm(forms.ModelForm):
    
    class Meta:
        model = UserAccount
        fields = ['image', 'first_name', 'last_name', 'email']
    




















