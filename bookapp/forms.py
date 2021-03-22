from django import forms

from .models import SpecialCategory, MainCategory, UnderCategory, Book, Cart, UserAccount, Checkout, Commentary


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
        fields = ['text',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].label = ''
        self.fields['text'].widget.attrs.update({'rows': 1, 'placeholder': 'write a comment'})









