from django import forms
from django.http import JsonResponse

from .models import SpecialCategory, MainCategory, BookCategory, Book, Cart, UserAccount, Checkout, Comment, User

import re


class FormWithValidator(forms.ModelForm):

    @staticmethod
    def name_validator(name, error_list):
        name = name.strip()
        if len(name.split(' ')) > 1:
            error_list.append(forms.ValidationError(
                f'"{name}" must be one word string'))
            return True
        return False

    def clean(self):
        cleaned_data = super().clean()
        error_list = []
        first_name = cleaned_data.get('first_name')
        second_name = cleaned_data.get('last_name')
        if self.name_validator(first_name, error_list) | self.name_validator(second_name, error_list):
            raise forms.ValidationError(error_list)


class UserAccountForm(FormWithValidator):

    class Meta:
        model = UserAccount
        fields = ['image', 'first_name', 'last_name', 'email']


class CheckoutForm(FormWithValidator):

    delivery_date = forms.DateField(
        widget=forms.TextInput(attrs={'type': 'date'}))

    class Meta:
        model = Checkout
        fields = ['first_name', 'last_name', 'email',
                  'address', 'delivery_date', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs.update({'rows': 3})


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['book_mark', 'text']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = ''
        self.fields['book_mark'].label = ''
        self.fields['text'].widget.attrs.update(
            {'rows': 1, 'placeholder': 'write a comment'})
        self.fields['book_mark'].widget.attrs.update({'max': 6, 'min': 1})

    def clean_book_mark(self, *args, **kwargs):
        value = self.cleaned_data['book_mark']
        if value > 5:
            raise forms.ValidationError(f'Max value is 5, you gived: {value}')
        return value

    def form_invalid(self):
        return JsonResponse({'status': 'form_invalid', 'errors': self.errors})


class LoginForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                f'There is no user with "{username}" username')
        else:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                raise forms.ValidationError('Incorrect password')


class RegistrForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'required': True})

    def clean_username(self):
        username = self.cleaned_data['username']
        errors = []
        if User.objects.filter(username=username):
            errors.append(forms.ValidationError(
                f'Username "{username}" is already taken'))
        if len(username.strip().split(' ')) > 1:
            errors.append(forms.ValidationError('Username must be one word string'))
        if errors:
            raise forms.ValidationError(errors)
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        reg_result = re.search(r'\w+@\w+\.\w+', email).group(0)
        errors = []
        if reg_result != email:
            errors.append(forms.ValidationError('Write valid email'))
        if UserAccount.objects.filter(email=email):
            errors.append(forms.ValidationError(
                f'User with "{email}" email already exist'))
        if errors:
            raise forms.ValidationError(errors)
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise forms.ValidationError('Password isn`t the same')
        return confirm_password
