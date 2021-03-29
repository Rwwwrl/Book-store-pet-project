from django import forms

from .models import SpecialCategory, MainCategory, UnderCategory, Book, Cart, UserAccount, Checkout, Commentary

from django.http import JsonResponse

class FormWithValidator(forms.ModelForm):

    @staticmethod
    def name_validator(name, error_list):
        name = name.strip()
        if len(name.split(' ')) > 1:
            error_list.append(forms.ValidationError(f'"{name}" must be one word string'))
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

    delivery_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

    class Meta:
        model = Checkout
        fields = ['first_name', 'last_name', 'email', 'address', 'delivery_date', 'commentary']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commentary'].widget.attrs.update({'rows': 3})


class CommentaryForm(forms.ModelForm):

    class Meta:
        model = Commentary
        fields = ['book_mark', 'text']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = ''
        self.fields['book_mark'].label = ''
        self.fields['text'].widget.attrs.update({'rows': 1, 'placeholder': 'write a comment'})
        self.fields['book_mark'].widget.attrs.update({'max': 6, 'min': 1})

    def clean_book_mark(self, *args, **kwargs):
        value = self.cleaned_data['book_mark']
        if value > 5:
            raise forms.ValidationError(f'Max value is 5, you gived: {value}')
        return value


    def form_invalid(self):
        return JsonResponse({'status': 'form_invalid', 'errors': self.errors})


