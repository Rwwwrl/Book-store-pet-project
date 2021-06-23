from bookapp.models import User, UserAccount
from django.test import TestCase

from datetime import date, timedelta
import json

from .forms import CommentForm, FormWithValidator, CheckoutForm, LoginForm, RegistrForm, UserAccountForm


class ServicesFuncTestCase(TestCase):

    def test_name_validator(self):
        invalid_name = 'test test'
        valid_name = 'test'
        error_list = []
        r_invalid = FormWithValidator.name_validator(invalid_name, error_list)
        r_valid = FormWithValidator.name_validator(valid_name, error_list)
        self.assertFalse(r_valid)
        self.assertTrue(r_invalid)


class UserAccountFormTestCase(TestCase):

    def test_clean_method(self):
        invalid_data = {
            'first_name': 'test test',
            'last_name': 'test'
        }
        valid_data = {
            'first_name': 'test',
            'last_name': 'test'
        }
        invalid_form = UserAccountForm(data=invalid_data)
        valid_form = UserAccountForm(data=valid_data)
        self.assertFalse(invalid_form.is_valid())
        self.assertTrue(valid_form.is_valid())
        self.assertEqual(invalid_form.errors['__all__'], ['"test test" must be one word string'])


class CheckoutFromTestData(TestCase):

    def test_clean_method(self):
        invalid_data = {
            'first_name': 'test_name test_name',
            'last_name': 'test_lastname test_lastname'
        }
        valid_data = {
            'first_name': 'test',
            'last_name': 'test'
        }

        required_data = {
            'email': 'test@test.com',
            'address': 'test address',
            'delivery_date': date.today() + timedelta(days=1)
        }

        for key in required_data:
            invalid_data[key] = required_data[key]
            valid_data[key] = required_data[key]

        valid_form = CheckoutForm(valid_data)
        invalid_form = CheckoutForm(invalid_data)
        self.assertTrue(valid_form.is_valid())
        self.assertFalse(invalid_form.is_valid())
        self.assertIn('"test_name test_name" must be one word string', invalid_form.errors['__all__'])
        self.assertIn('"test_lastname test_lastname" must be one word string', invalid_form.errors['__all__'])



    def test_field_widget(self):
        form = CheckoutForm()
        self.assertEqual(form.fields['delivery_date'].widget.input_type, 'date')
        self.assertEqual(form.fields['comment'].widget.attrs.get('rows', ''), 3)


class CommentFormTestData(TestCase):

    form = CommentForm

    def test_init_method(self):
        self.assertEqual(self.form().fields['text'].label, '')
        self.assertEqual(self.form().fields['book_mark'].label, '')
        self.assertEqual(self.form().fields['text'].widget.attrs['rows'], 1)
        self.assertEqual(self.form().fields['text'].widget.attrs['placeholder'], 'write a comment')
        self.assertEqual(self.form().fields['book_mark'].widget.attrs['max'], 6)
        self.assertEqual(self.form().fields['book_mark'].widget.attrs['min'], 1)

    def test_clean_book_mark_method(self):
        invalid_data = {'book_mark': 6, 'text': 'test'}
        valid_data = {'book_mark': 5, 'text': 'test'}
        invalid_form = self.form(invalid_data)
        valid_form = self.form(valid_data)
        self.assertTrue(valid_form.is_valid())
        self.assertFalse(invalid_form.is_valid())
        self.assertEqual(invalid_form.errors['book_mark'], ['Max value is 5, you gived: 6'])
    
    def test_form_invalid_method(self):
        invalid_data = {'book_mark': 6, 'text': 'test'}
        invalid_form = self.form(invalid_data)
        responce = invalid_form.form_invalid()
        json_string = json.loads(responce.content)        
        self.assertTrue(json_string['status'], 'form_invalid')
        self.assertTrue(json_string['errors'], 'Max value is 5, you gived: 6')


class LoginFormTestCase(TestCase):

    form = LoginForm

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='user', password='123456')

    def test_init_fields(self):
        self.assertEqual(self.form().fields['password'].widget.input_type, 'password')

    def test_clean_method(self):
        valid_name_invalid_password = {
            'username': 'user',
            'password': 'test'
        } 
        invalid_name_valid_password = {
            'username': 'username',
            'password': '123456'
        }
        valid_data = {
            'username': 'user',
            'password': '123456'
        } 
        invalid_name = self.form(invalid_name_valid_password)
        invalid_password = self.form(valid_name_invalid_password)
        valid_form = self.form(valid_data)

        self.assertTrue(valid_form.is_valid())
        self.assertFalse(invalid_name.is_valid())
        self.assertFalse(invalid_password.is_valid())
        
        self.assertIn('Incorrect password', invalid_password.errors['__all__'])
        self.assertIn('There is no user with "username" username', invalid_name.errors['__all__'])


class RegistrFormTestCase(TestCase):

    form = RegistrForm


    @staticmethod
    def get_valid_required_data(*fields):
        full_valid_data = {
            'username': 'username',
            'email': 'email@email.com',
            'password': '123456',
            'confirm_password': '123456'
        }
        r = {}
        for i in fields:
            if not i in full_valid_data:
                raise ValueError(f'RegistForm doesn`t have "{i}" field')
            r[i] = full_valid_data[i]
        return r

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='user', password='123456') 
        UserAccount.objects.create(user=user, email='test@test.com')


    def test_init_fields(self):
        self.assertEqual(self.form().fields['password'].widget.input_type, 'password')
        self.assertEqual(self.form().fields['confirm_password'].widget.input_type, 'password')
        self.assertTrue(self.form().fields['email'].widget.attrs['required'])

    def test_clean_username_method(self):
        required_data = self.get_valid_required_data('email', 'password', 'confirm_password')
        existing_username = 'user'
        free_username = 'username'
        two_word_username = 'user user'

        existing_username_data = required_data.copy()
        two_word_username_data = required_data.copy()
        valid_data = required_data.copy()

        existing_username_data['username'] = existing_username
        two_word_username_data['username'] = two_word_username
        valid_data['username'] = free_username
        
        two_word_username_form = self.form(two_word_username_data)
        existing_username_form = self.form(existing_username_data)
        valid_form = self.form(valid_data)
        
        self.assertFalse(two_word_username_form.is_valid())
        self.assertFalse(existing_username_form.is_valid())
        self.assertTrue(valid_form.is_valid())

        self.assertEqual(existing_username_form.errors['username'], ['Username "user" is already taken'])
        self.assertEqual(two_word_username_form.errors['username'], ['Username must be one word string'])

    def test_clean_email_method(self):
        required_data = self.get_valid_required_data('username', 'password', 'confirm_password')
        invalid_email = 'email@.com'
        existing_email = 'test@test.com'
        valid_email = 'email@email.com'

        invalid_email_data = required_data.copy()
        existing_email_data = required_data.copy()
        valid_email_data = required_data.copy()

        invalid_email_data['email'] = invalid_email
        existing_email_data['email'] = existing_email
        valid_email_data['email'] = valid_email

        invalid_email_form = self.form(invalid_email_data)
        existing_email_form = self.form(existing_email_data)
        valid_email_form = self.form(valid_email_data)

        self.assertFalse(invalid_email_form.is_valid())
        self.assertFalse(existing_email_form.is_valid())
        self.assertTrue(valid_email_form.is_valid())

        self.assertEqual(invalid_email_form.errors['email'], ['Enter a valid email address.'])
        self.assertEqual(existing_email_form.errors['email'], ['User with "test@test.com" email already exist'])
 
    def test_clean_confirm_password_method(self):
        required_data = self.get_valid_required_data('username', 'email', 'password')
        invalid_password = 'not the same password'
        valid_password = '123456'
        invalid_password_data = required_data.copy()
        valid_password_data = required_data.copy()
        invalid_password_data['confirm_password'] = invalid_password
        valid_password_data['confirm_password'] = valid_password
        invalid_password_form = self.form(invalid_password_data)
        valid_password_form = self.form(valid_password_data)

        self.assertFalse(invalid_password_form.is_valid())
        self.assertTrue(valid_password_form.is_valid())
        self.assertEqual(invalid_password_form.errors['confirm_password'], ['Password isn`t the same'])






