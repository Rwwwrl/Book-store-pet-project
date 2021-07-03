from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib import auth
from django.http.response import Http404

import json
from datetime import date, timedelta

from .models import Checkout, Comment, User, SpecialCategory, Book
from .forms import CommentForm
from services.services import *


def get_messages_from_storage(storage):
    return [str(i) for i in storage]


class ClassForTestServices():
    pass


class UserMixinTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='username', password='123')
        cls.url = reverse('tests:user-mixin-test')

    def test_context_without_login(self):
        r = self.client.get(self.url)
        self.assertEqual('AnonymousUser', str(r.context['user']))
        self.assertNotIn('wishlist_from_dispatch', r.context)
        self.assertNotIn('cart_from_dispatch', r.context)
        self.assertNotIn('account_from_dispatch', r.context)

        self.assertIn('main_categorys', r.context)

    def test_mixin_with_login(self):
        login = self.client.login(username='username', password='123')
        r = self.client.get(self.url)
        self.assertEqual('username', str(r.context['user']))
        self.assertIn('wishlist_from_dispatch', r.context)
        self.assertIn('cart_from_dispatch', r.context)
        self.assertIn('account_from_dispatch', r.context)

        self.assertIn('wishlist', r.context)
        self.assertIn('cart', r.context)
        self.assertIn('cart_final_price', r.context)


class QuerySetForMainPageTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sp = SpecialCategory.objects.create(title='title', slug='slug')
        for i in range(3):
            book = Book.objects.create(title=f'title{i}', info=f'info{i}')
            cls.sp.books.add(book)

    def setUp(self):
        self.instance = ClassForTestServices()

    def test_with_slug(self):
        slug = 'slug'
        get_queryset_for_main_page(self.instance, slug)
        self.assertEqual(self.instance.special_category, self.sp)
        self.assertQuerysetEqual(self.instance.queryset, self.sp.books.all())
        self.assertTrue(self.instance.is_it_special)

    def test_without_slug(self):
        books = Book.objects.all()
        get_queryset_for_main_page(self.instance)
        self.assertIsNone(self.instance.special_category)
        self.assertQuerysetEqual(self.instance.queryset, books)
        self.assertFalse(self.instance.is_it_special)


class SaveCommentAndReturnCommentModelTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        valid_data = {
            'book_mark': 5,
            'text': 'test'
        }
        cls.form = CommentForm(valid_data)
        cls.instance = ClassForTestServices()
        cls.instance.object = Book.objects.create(title='title', info='info')
        cls.user = User.objects.create_user(username='user', password='123')
        acc = UserAccount.objects.create(user=cls.user)
        cls.instance.account = acc

    def test_save_comment_and_return_comment_model_method(self):
        model = save_comment_and_return_comment_model(self.instance, self.form)
        self.assertTrue(isinstance(model, Comment))
        self.assertEqual(model.user_account, self.instance.account)
        self.assertEqual(model.book, self.instance.object)


class JsonResponceTestCase(SaveCommentAndReturnCommentModelTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.instance.user = cls.user
        for i in range(5):
            comment = Comment.objects.create(
                book=cls.instance.object,
                user_account=cls.instance.account,
                book_mark=i
            )
            cls.instance.object.comments.add(comment)

        wishlist = WishList.objects.create(user=cls.instance.user)
        wishlist.books.add(cls.instance.object)
        cls.instance.wishlist = wishlist

    def test_json_responce_method(self):
        model = save_comment_and_return_comment_model(self.instance, self.form)
        url = reverse('book_comments', kwargs={
            'book_slug': model.book.slug})
        r = json_responce(self.instance, model)
        json_data = json.loads(r.content)
        self.assertTrue(json_data['good'])
        comment_info = json_data['comment_info']
        self.assertEqual(comment_info['profile_image'],
                         self.instance.account.image.url)
        self.assertEqual(
            comment_info['profile_username'], self.instance.user.username)
        self.assertEqual(
            comment_info['date_of_creation'], model.date_of_creation.strftime('%B %d, %Y'))
        self.assertEqual(comment_info['text'], model.text)
        self.assertEqual(comment_info['book_mark'], model.book_mark)
        self.assertEqual(comment_info['url'], url)

    def test_is_book_on_wishlist(self):
        self.assertTrue(is_book_on_wishlist(self.instance))

    def test_get_book_comments(self):
        r = self.instance.object.comments.all().order_by('id')[:5]
        self.assertQuerysetEqual(get_book_comments(self.instance), r)

    def test_get_also_like_books_queryset_with_bookcategories(self):
        querySet = []
        for i in range(2):
            bc = BookCategory.objects.create(title=f'title{i}')
            for j in range(2):
                book = Book.objects.create(title=f'title{j}', info=f'info{j}')
                bc.books.add(book)
                querySet.append(book)
            self.instance.object.bookcategories.add(bc)
        r = sorted(querySet, key=lambda book: book.mark)
        self.assertEqual(r, get_also_like_books_queryset(self.instance))

    def test_get_also_like_books_queryset_without_bookcategories(self):
        self.assertEqual(len(self.instance.object.bookcategories.all()), 0)
        self.assertEqual(get_also_like_books_queryset(self.instance), [])


class AddOrDeleteBookFromWishListTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.instance = ClassForTestServices()
        user = User.objects.create_user(username='user', password='123')
        wishlist = WishList.objects.create(user=user)
        cls.instance.wishlist = wishlist
        books = []

        for i in range(2):
            b = Book.objects.create(
                title=f'title{i}', slug=f'slug{i}', info=f'info{i}')
            books.append(b)

        cls.instance.wishlist.books.add(books[0])

    def test_add_book_that_already_in_wishlist(self):
        book = Book.objects.get(slug='slug0')
        self.assertIn(book, self.instance.wishlist.books.all())
        r = self.client.get(
            reverse('add_to_wishlist', kwargs={'book_slug': 'slug0'}))
        add_book_to_wishlist(self.instance, r.wsgi_request, 'slug0')
        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0], 'You already added this book to wishlist')

    def test_add_book_that_not_in_wishlist(self):
        book = Book.objects.get(slug='slug1')
        self.assertNotIn(book, self.instance.wishlist.books.all())
        r = self.client.get(
            reverse('add_to_wishlist', kwargs={'book_slug': 'slug1'}))
        add_book_to_wishlist(self.instance, r.wsgi_request, 'slug1')
        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'Added to wish list')
        self.assertIn(book, self.instance.wishlist.books.all())

    def test_delete_book_that_in_wishlist(self):
        book = Book.objects.get(slug='slug0')
        self.assertIn(book, self.instance.wishlist.books.all())
        r = self.client.get(reverse('remove_from_wishlist',
                            kwargs={'book_slug': 'slug0'}))
        delete_book_from_wishlist(self.instance, r.wsgi_request, 'slug0')
        self.assertNotIn(book, self.instance.wishlist.books.all())

    def test_delete_book_that_not_in_wishlist(self):
        book = Book.objects.get(slug='slug1')
        self.assertNotIn(book, self.instance.wishlist.books.all())
        r = self.client.get(reverse('remove_from_wishlist',
                            kwargs={'book_slug': 'slug1'}))
        delete_book_from_wishlist(self.instance, r.wsgi_request, 'slug1')
        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'This book isn`t on your wishlist')
        self.assertNotIn(book, self.instance.wishlist.books.all())


class RecalCartViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='user', password='123456')
        cls.cart = Cart.objects.create(user=user)
        book = Book.objects.create(title='title', info='info')
        cls.cart_item = CartItem.objects.create(book=book, cart=cls.cart)

    def test_update_cart_item_quantity(self):
        self.assertIsNotNone(self.cart.cart_items.filter(book_id=1))
        self.assertEqual(self.cart_item.qty, 1)
        test_valid_id_data = {
            '1': 3
        }
        test_invalid_id_data = {
            '2': 4
        }
        update_cart_item_quantity('1', self.cart, test_valid_id_data)
        self.cart_item.refresh_from_db(fields=['qty'])
        self.assertEqual(self.cart_item.qty, 3)
        with self.assertRaises(Http404):
            update_cart_item_quantity('2', self.cart, test_invalid_id_data)


class AddOrRemoveBookFromCartTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username='user', password='123')
        cart = Cart.objects.create(user=user)
        cls.instance = ClassForTestServices()
        cls.instance.cart = cart
        cls.book = Book.objects.create(
            title='title',
            slug='slug',
            info='info'
        )

    def test_add_book_that_not_in_cart(self):
        self.assertEqual(
            len(self.instance.cart.cart_items.filter(book__slug='slug')), 0)
        r = self.client.get(
            reverse('add_to_cart', kwargs={'book_slug': 'slug'}))
        add_book_to_cart(self.instance, r.wsgi_request, 'slug')
        self.assertEqual(
            len(self.instance.cart.cart_items.filter(book__slug='slug')), 1)
        cart_item = self.instance.cart.cart_items.get(book__slug='slug')
        self.assertEqual(cart_item.qty, 1)
        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'Book added to cart')

    def test_add_book_that_already_in_cart(self):
        cart_item = CartItem.objects.create(
            book=self.book, qty=1, cart=self.instance.cart
        )
        self.assertEqual(
            len(self.instance.cart.cart_items.filter(book__slug='slug')), 1)
        self.assertEqual(cart_item.qty, 1)
        r = self.client.get(
            reverse('add_to_cart', kwargs={'book_slug': 'slug'}))
        add_book_to_cart(self.instance, r.wsgi_request, 'slug')
        cart_item2 = self.instance.cart.cart_items.get(book=self.book)
        self.assertEqual(cart_item2.qty, 2)
        self.assertEqual(
            len(self.instance.cart.cart_items.filter(book__slug='slug')), 1)
        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0], 'The cart already contains this book, the qty has been increased by 1')

    def test_remove_book_from_cart(self):
        cart_item = CartItem.objects.create(
            book=self.book, qty=1, cart=self.instance.cart
        )
        self.assertTrue(self.instance.cart.cart_items.filter(
            id=cart_item.id).exists())
        remove_book_from_cart(self.instance, cart_item.id)
        self.assertFalse(self.instance.cart.cart_items.filter(
            id=cart_item.id).exists())
        self.assertFalse(CartItem.objects.filter(
            book=self.book, cart=self.instance.cart).exists())


class CartViewServicesTestData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.instance = ClassForTestServices()
        user = User.objects.create_user(username='user', password='123')
        user_acc = UserAccount.objects.create(user=user)
        cart = Cart.objects.create(user=user)
        cls.instance.account = user_acc
        cls.instance.cart = cart

    def test_save_checkout(self):
        valid_data = {
            'first_name': 'test',
            'last_name': 'test',
            'email': 'test@test.com',
            'address': 'test address',
            'delivery_date': date.today() + timedelta(days=1)
        }
        self.assertFalse(self.instance.cart.is_used)
        self.assertFalse(Checkout.objects.all().exists())
        form = CheckoutForm(valid_data)
        save_checkout(self.instance, form)
        checkout_model = Checkout.objects.first()
        self.assertEqual(checkout_model.cart, self.instance.cart)
        self.assertEqual(checkout_model.user_account, self.instance.account)
        self.assertTrue(self.instance.cart.is_used)


class SearchViewServicesTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        BookCategory.objects.create(title='title')
        BookCategory.objects.create(title='title_1', slug='title')

    def test_get_filtered_by_slug_or_title_queryset(self):
        r = [BookCategory.objects.get(
            title='title'), BookCategory.objects.get(slug='title')]
        self.assertEqual(r, get_filtered_by_slug_or_title_queryset(
            BookCategory.objects, 'title'))

    def test_get_search_results_func(self):
        data = 'title'
        bookcategory_queryset = get_filtered_by_slug_or_title_queryset(
            BookCategory.objects, data)
        special_category_queryset = get_filtered_by_slug_or_title_queryset(
            SpecialCategory.objects, data)
        book_queryset = get_filtered_by_slug_or_title_queryset(
            Book.objects, data)
        category_queryset = bookcategory_queryset + special_category_queryset
        r = [category_queryset, book_queryset]
        self.assertEqual(r, get_search_results(data))


class LoginViewServicesTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='123')

    def test_authenticate_and_login_user_with_valid_data(self):
        r = self.client.get(reverse('login'))
        self.assertFalse(r.wsgi_request.user.is_authenticated)
        authenticate_and_login_user(
            r.wsgi_request, 'user', '123', 'message_text')
        self.assertTrue(r.wsgi_request.user.is_authenticated)
        self.assertEqual(r.wsgi_request.user.username, 'user')

        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'message_text')

    def test_authenticate_and_login_user_with_invalid_data(self):
        r = self.client.get(reverse('login'))
        self.assertFalse(r.wsgi_request.user.is_authenticated)
        authenticate_and_login_user(
            r.wsgi_request, 'wrong_user', '123', 'message_text')
        self.assertFalse(r.wsgi_request.user.is_authenticated)

        storage = get_messages(r.wsgi_request)
        messages = get_messages_from_storage(storage)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'You had not logged, wrong data')


class RegistrationViewServicesTestCase(TestCase):

    def test_register_user_func(self):
        valid_data = {
            'username': 'username',
            'email': 'email@email.com',
            'password': '123456',
            'confirm_password': '123456'
        }
        form = RegistrForm(valid_data)
        self.assertEqual(len(User.objects.all()), 0)
        user_model = register_user(form)
        self.assertEqual(len(User.objects.all()), 1)
        self.assertEqual(User.objects.get(username='username'), user_model)
