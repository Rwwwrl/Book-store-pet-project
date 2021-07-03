from django.http import response
from django.test import TestCase, RequestFactory
from django.urls.base import reverse
from django.http.response import JsonResponse
from django.contrib.messages import get_messages

import json
from datetime import date, timedelta

from .models import Book, BookCategory, CartItem, Comment, SpecialCategory, User, UserAccount, WishList
from .views import AccountView, AddToCart, AddToWishList, BookCategoryDetail, BookComments, BookDetail, CheckoutsHistoryView, DeleteFromWishList, MainPage, RemoveFromCart
from .test_services import get_messages_from_storage


class MainPageViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(5):
            Book.objects.create(
                title=f'title{i}',
                info='info'
            )
        cls.url = reverse('main_page')
        SpecialCategory.objects.create(
            title='sp_title',
            slug='sp_slug'
        )

    def test_right_url_and_reverse(self):
        r = self.client.get('/main-page/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.resolver_match.func.__name__,
                         MainPage.as_view().__name__)

    def test_right_url_and_reverse_with_special_category_slug(self):
        r = self.client.get('/main_page/sp_slug/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get(reverse('special_category_page', kwargs={
            'special_category_slug': 'sp_slug'
        }))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.resolver_match.func.__name__,
                         MainPage.as_view().__name__)

    def test_template_name(self):
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/main_page.html')

    def test_pagination(self):
        r = self.client.get(self.url)
        self.assertIn('is_paginated', r.context)
        self.assertTrue(r.context['is_paginated'])
        self.assertEqual(len(r.context['page_obj']), 4)
        r_next_page = self.client.get(self.url + '?page=2')
        self.assertEqual(r_next_page.status_code, 200)
        self.assertIn('is_paginated', r_next_page.context)
        self.assertTrue(r.context['is_paginated'])
        self.assertEqual(len(r_next_page.context['page_obj']), 1)

    def test_default_context(self):
        r = self.client.get(self.url)
        self.assertIn('special_categorys', r.context)
        self.assertIn('is_it_special', r.context)
        self.assertIn('special_category', r.context)
        self.assertQuerysetEqual(
            r.context['special_categorys'], SpecialCategory.objects.all())

    def test_context_without_special_category_slug(self):
        r = self.client.get(self.url)
        self.assertFalse(r.context['is_it_special'])
        self.assertIsNone(r.context['special_category'])

    def test_context_with_special_category_slug(self):
        r = self.client.get('/main_page/sp_slug/')
        special_category = SpecialCategory.objects.get(slug='sp_slug')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['is_it_special'])
        self.assertEqual(r.context['special_category'], special_category)


class BookDetailViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        Book.objects.create(title='title', slug='slug')
        User.objects.create_user(username='user', password='123456')
        cls.url = reverse('book_detail', kwargs={'book_slug': 'slug'})

    def test_url_and_reverse(self):
        r = self.client.get('/main-page/books/slug/')
        self.assertEqual(r.status_code, 200)
        r_reverse = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

        self.assertEqual(r.resolver_match.func.__name__, BookDetail.as_view().__name__) 
        self.assertEqual(r_reverse.resolver_match.func.__name__, BookDetail.as_view().__name__) 

    def test_template(self):
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/book_detail.html')

    def test_default_context_without_login(self):
        r = self.client.get(self.url)
        self.assertEqual(str(r.context['user']), 'AnonymousUser')
        self.assertIn('comments', r.context)
        self.assertIn('comment_form', r.context)
        self.assertIn('you_may_also_like_books', r.context)
        self.assertIn('book', r.context)

    def test_context_with_login(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertIn('is_book_on_wishlist', r.context)
        self.assertIn('count_in_cart', r.context)

    def test_post_request_without_login(self):
        r = self.client.post(self.url,  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, '/login/')

    def test_post_invalid_form_request_with_login(self):
        self.client.login(username='user', password='123456')
        invalid_data = {'book_mark': 6, 'text': 'test'}
        r = self.client.post(self.url, invalid_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(isinstance(r, JsonResponse))
        json_data = json.loads(r.content)
        self.assertEqual(json_data['status'], 'form_invalid')
        self.assertEqual(json_data['errors']['book_mark'], ['Max value is 5, you gived: 6'])

    def test_post_valid_form_request_with_login(self):
        self.client.login(username='user', password='123456')
        valid_data = {'book_mark': 5, 'text': 'test'}
        r = self.client.post(self.url, valid_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(isinstance(r, JsonResponse))
        json_data = json.loads(r.content)
        self.assertTrue(json_data['good'])
        self.assertIn('comment_info', json_data)


class BookCategoryDetailViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        category = BookCategory.objects.create(title='title', slug='book_category_slug')
        for i in range(12):
            book = Book.objects.create(
                title=f'title{i}',
                info='info'
            )
            category.books.add(book)
        cls.url = reverse('bookcategory_page', kwargs={'bookcategory_slug': 'book_category_slug'})

    def test_url_and_reverse(self):
        r = self.client.get('/main-page/book_category_slug/')
        self.assertEqual(r.status_code, 200)
        r_reverse = self.client.get(self.url) 
        self.assertEqual(r_reverse.status_code, 200)
        self.assertEqual(r.resolver_match.func.__name__, BookCategoryDetail.as_view().__name__)
        self.assertEqual(r_reverse.resolver_match.func.__name__, BookCategoryDetail.as_view().__name__)

    def test_template(self):
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/bookcategory_books.html')

    def test_context(self):
        r = self.client.get(self.url)
        self.assertIn('books', r.context)
        self.assertIn('category_title', r.context)

    def test_paginate(self):
        r = self.client.get(self.url)
        self.assertIn('is_paginated', r.context)
        self.assertEqual(len(r.context['books']), 10)
        r_next_page = self.client.get(self.url + '?page=2')
        self.assertEqual(r_next_page.status_code, 200) 
        self.assertIn('is_paginated', r_next_page.context)
        self.assertEqual(len(r_next_page.context['books']), 2)


class AddAndDeleteFromWishListViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        Book.objects.create(title='title', slug='slug')
        User.objects.create_user(username='user', password='123456')
        cls.add_url = reverse('add_to_wishlist', kwargs={'book_slug': 'slug'})
        cls.remove_url = reverse('remove_from_wishlist', kwargs={'book_slug': 'slug'})

    def test_url_and_reverse_with_login(self):
        self.client.login(username='user', password='123456')

        r_add = self.client.get('/add_to_wishlist/slug/')        
        r_add_reverse = self.client.get(self.add_url)
        self.assertEqual(r_add.status_code, 302)
        self.assertRedirects(r_add, reverse('book_detail', kwargs={'book_slug': 'slug'}))
        self.assertEqual(r_add_reverse.status_code, 302)
        self.assertRedirects(r_add_reverse, reverse('book_detail', kwargs={'book_slug': 'slug'}))
        self.assertEqual(r_add.resolver_match.func.__name__, AddToWishList.as_view().__name__)
        self.assertEqual(r_add_reverse.resolver_match.func.__name__, AddToWishList.as_view().__name__)

        r_remove = self.client.get('/remove_from_wishlist/slug/')        
        r_remove_reverse = self.client.get(self.remove_url)
        self.assertEqual(r_remove.status_code, 302)
        self.assertRedirects(r_remove, reverse('wishlist_page'))
        self.assertEqual(r_remove_reverse.status_code, 302)
        self.assertRedirects(r_remove_reverse, reverse('wishlist_page'))
        self.assertEqual(r_remove.resolver_match.func.__name__, DeleteFromWishList.as_view().__name__)
        self.assertEqual(r_remove_reverse.resolver_match.func.__name__, DeleteFromWishList.as_view().__name__)

    def test_reverse_without_login(self):
        r_add = self.client.get(self.add_url)
        self.assertEqual(r_add.status_code, 302)
        self.assertRedirects(r_add, '/login/?next=/add_to_wishlist/slug/')

        r_remove = self.client.get(self.remove_url)
        self.assertEqual(r_remove.status_code, 302)
        self.assertRedirects(r_remove, '/login/?next=/remove_from_wishlist/slug/')


class AddAndRemoveFromCartViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        Book.objects.create(title='title', slug='slug')
        User.objects.create_user(username='user', password='123456')
        cls.add_url = reverse('add_to_cart', kwargs={'book_slug': 'slug'})
        cls.remove_url = reverse('remove_from_cart', kwargs={'id': 1})

    def test_url_and_reverse_with_login(self):
        self.client.login(username='user', password='123456')

        r_add = self.client.get('/add_to_cart/slug/')        
        r_add_reverse = self.client.get(self.add_url)
        self.assertEqual(r_add.status_code, 302)
        self.assertRedirects(r_add, reverse('book_detail', kwargs={'book_slug': 'slug'}))
        self.assertEqual(r_add_reverse.status_code, 302)
        self.assertRedirects(r_add_reverse, reverse('book_detail', kwargs={'book_slug': 'slug'}))
        self.assertEqual(r_add.resolver_match.func.__name__, AddToCart.as_view().__name__)
        self.assertEqual(r_add_reverse.resolver_match.func.__name__, AddToCart.as_view().__name__)

        r_remove = self.client.get('/remove_from_cart/1/')        
        r_remove_reverse = self.client.get(self.remove_url)
        self.assertEqual(r_remove.status_code, 302)
        self.assertRedirects(r_remove, reverse('cart_page'))
        self.assertEqual(r_remove_reverse.status_code, 302)
        self.assertRedirects(r_remove_reverse, reverse('cart_page'))
        self.assertEqual(r_remove.resolver_match.func.__name__, RemoveFromCart.as_view().__name__)
        self.assertEqual(r_remove_reverse.resolver_match.func.__name__, RemoveFromCart.as_view().__name__)

    def test_reverse_without_login(self):
        r_add = self.client.get(self.add_url)
        self.assertEqual(r_add.status_code, 302)
        self.assertRedirects(r_add, '/login/?next=/add_to_cart/slug/')

        r_remove = self.client.get(self.remove_url)
        self.assertEqual(r_remove.status_code, 302)
        self.assertRedirects(r_remove, '/login/?next=/remove_from_cart/1/')


class WishListViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='user', password='123456')
        wishlist = WishList.objects.create(user=user)
        for i in range(9):
            book = Book.objects.create(title=f'title{i}', info='info') 
            wishlist.books.add(book) 
        cls.url = reverse('wishlist_page')

    def test_url_and_reverse_without_login(self):
        r = self.client.get('/account_page/wishlist/') 
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, '/login/?next=/account_page/wishlist/')

    def test_url_and_reverse_with_login(self):
        self.client.login(username='user', password='123456')
        r = self.client.get('/account_page/wishlist/') 
        self.assertEqual(r.status_code, 200)
        r_reverse = self.client.get(self.url) 
        self.assertEqual(r_reverse.status_code, 200)

    def test_template(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/account_page/wish_page.html')

    def test_paginate(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertIn('books', r.context)
        self.assertIn('is_paginated', r.context)
        self.assertEqual(len(r.context['books']), 8)

        r_next_page = self.client.get(self.url + '?page=2')
        self.assertEqual(r_next_page.status_code, 200)
        self.assertIn('is_paginated', r.context)
        self.assertEqual(len(r_next_page.context['books']), 1)


class CartViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='user', password='123456')
        cls.url = reverse('cart_page')

    def test_reverse_and_url_without_login(self):
        r = self.client.get('/account_page/cart_page/')
        r_reverse = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r_reverse.status_code, 302)
        self.assertRedirects(r, '/login/?next=/account_page/cart_page/')
        self.assertRedirects(r_reverse, '/login/?next=/account_page/cart_page/')

    def test_template(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/account_page/cart_page.html')

    def test_context(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertIn('cart_final_qty', r.context)
        self.assertIn('cart_products', r.context)
        self.assertIn('checkout_form', r.context)

    def test_post_with_invalid_form(self):
        self.client.login(username='user', password='123456')
        invalid_data = {
            'first_name': 'test_name test_name',
            'last_name': 'test_lastname test_lastname',
            'email': 'test@test.com',
            'address': 'test address',
            'delivery_date': date.today() + timedelta(days=1)
        }
        r = self.client.post(self.url, invalid_data)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'bookapp/account_page/cart_page.html')

        self.assertFormError(r, 'checkout_form', None, ['"test_name test_name" must be one word string', '"test_lastname test_lastname" must be one word string'])

    def test_post_with_valid_form(self):
        self.client.login(username='user', password='123456')
        valid_data = {
            'first_name': 'test_name',
            'last_name': 'test_lastname',
            'email': 'test@test.com',
            'address': 'test address',
            'delivery_date': date.today() + timedelta(days=1)
        }
        r = self.client.post(self.url, valid_data)
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, reverse('main_page'))
        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage) 
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'You have succesfully placed an order')


class RecalcCartView(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='user', password='123456')
        cls.url = reverse('recalc_cart')

    def test_url_and_reverse_with_login(self):
        self.client.login(username='user', password='123456')
        r = self.client.post('/account_page/cart_page/recalt_cart/')

        r_reverse = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r_reverse.status_code, 302)
        self.assertRedirects(r, reverse('cart_page'))
        self.assertRedirects(r_reverse, reverse('cart_page'))

    def test_url_without_login(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, '/login/?next=/account_page/cart_page/recalt_cart/')
    
    def test_post_with_invalid_data(self):
        invalid_data = {
            '1': 2
        }
        self.client.login(username='user', password='123456')
        r = self.client.post(self.url, invalid_data)
        self.assertEqual(r.status_code, 404)


class AccountViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='user', password='123456')
        cls.url = reverse('account_page')

    def test_reverse_and_url_with_login(self):
        self.client.login(username='user', password='123456')
        r = self.client.get('/account_page/account/') 
        r_reverse = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r_reverse.status_code, 200)
        self.assertEqual(r.resolver_match.func.__name__, AccountView.as_view().__name__)        
        self.assertEqual(r_reverse.resolver_match.func.__name__, AccountView.as_view().__name__)        

    def test_redirect_to_login_page(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, '/login/?next=/account_page/account/')

    def test_right_template_used(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/account_page/account_page.html')

    def test_context(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertIn('form', r.context)
        self.assertIn('account', r.context)

    def test_post_with_valid_form(self):
        valid_data = {
            'first_name': 'test',
            'last_name': 'test'
        }
        self.client.login(username='user', password='123456')
        r = self.client.post(self.url, valid_data)
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, reverse('account_page'))
        
        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'Your profile settings saved')

    def test_post_with_invalid_form(self):
        invalid_data = {
            'first_name': 'test test',
            'last_name': 'test'
        }
        self.client.login(username='user', password='123456')
        r = self.client.post(self.url, invalid_data)
        self.assertTemplateUsed(r, 'bookapp/account_page/account_page.html') 
        self.assertFormError(r, 'form', None, ['"test test" must be one word string'])


class CheckoutsHistoryViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='user', password='123456')
        cls.url = reverse('checkouts_page') 

    def test_url_with_login(self):
        self.client.login(username='user', password='123456')
        r = self.client.get('/account_page/checkout_history/')
        r_reverse = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r_reverse.status_code, 200)

        self.assertEqual(r.resolver_match.func.__name__, CheckoutsHistoryView.as_view().__name__)

    def test_redirect_without_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertRedirects(r, '/login/?next=/account_page/checkout_history/') 

    def test_context_and_template(self):
        self.client.login(username='user', password='123456')
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/account_page/checkouts.html')         
        self.assertIn('checkouts', r.context)


class BookCommentsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='user', password='123456')
        book = Book.objects.create(title='title', slug='slug', info='info')
        user_account = UserAccount.objects.create(user=user)
        for i in range(6):
            comment = Comment.objects.create(
                book=book,
                user_account=user_account,
                text='text'
            )
        cls.url = reverse('book_comments', kwargs={'book_slug': 'slug'})
    
    def test_reverse_and_url(self):
        r = self.client.get('/slug/comments/')
        r_reverse = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r_reverse.status_code, 200)

    def test_template(self):
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'bookapp/book_comments.html')

    def test_context(self):
        r = self.client.get(self.url)
        self.assertIn('book', r.context)
        self.assertIn('comments', r.context)
        
    def test_pagination(self):
        r = self.client.get(self.url)
        self.assertIn('is_paginated', r.context)
        self.assertEqual(len(r.context['comments']), 5)
        r_next_page = self.client.get(self.url + '?page=2')
        self.assertIn('is_paginated', r_next_page.context)
        self.assertEqual(len(r_next_page.context['comments']), 1)

 


