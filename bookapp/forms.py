from django import forms

from .models import SpecialCategory, MainCategory, UnderCategory, Book, Cart, UserAccount, Checkout, Commentary

from django.http import JsonResponse

class UserAccountForm(forms.ModelForm):
    
    class Meta:
        model = UserAccount
        fields = ['image', 'first_name', 'last_name', 'email']
    

class CheckoutForm(forms.ModelForm):

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
        self.fields['book_mark'].widget.attrs.update({'max': 6})

    def clean__book_mark(self, *args, **kwargs):
        value = self.cleaned_data['book_mark']
        if value > 5:
            raise forms.ValidationError(f'Max value is 5, you gived: {value}')
        return value


    def form_invalid(self):
        return JsonResponse({'status': 'form_invalid', 'errors': self.errors})





