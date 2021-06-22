from django.test import TestCase
from django.core.files import File
from django.urls import reverse

from decimal import *
import sys
import os

from .models import Book, Cart, CartItem, SpecialCategory, MainCategory, BookCategory, User, UserAccount, WishList, Comment, Checkout


sys.path.append('..')


class CategoryTest(TestCase):

    def setUp(self):
        self.spec_c = SpecialCategory.objects.create(
            title='title', slug='slug')
        self.book_c = BookCategory.objects.create(title='title', slug='slug')
        self.main_c = MainCategory.objects.create(title='title', slug='slug')

    def test_slug_is_not_none_after_save(self):
        categories = [self.spec_c, self.book_c, self.main_c]
        for c in categories:
            c.slug = None
            c.save(update_fields=['slug'])
            self.assertNotEqual(c.slug, '')

    def test_categories_get_absolute_url(self):
        self.assertEqual(self.spec_c.get_absolute_url(),
                         f'/main_page/{self.spec_c.slug}/')
        self.assertEqual(self.book_c.get_absolute_url(),
                         f'/main-page/{self.book_c.slug}/')
        self.assertFalse(hasattr(self.main_c, 'get_absolute_url'))

    def test_get_books_count(self):
        book = Book.objects.create(title='title', info='info')
        self.book_c.books.set([book])
        self.assertEqual(self.book_c.get_books_count(), 1)

    def test_add_and_remove_main_category_from_book_category(self):
        self.book_c.main_category = self.main_c
        self.book_c.save(update_fields=['main_category'])
        self.assertEqual(self.book_c.main_category, self.main_c)
        self.assertEqual(len(self.main_c.bookcategories.all()), 1)
        self.main_c.delete()
        self.assertEqual(len(MainCategory.objects.all()), 0)
        self.assertEqual(len(BookCategory.objects.all()), 0)


class WishListTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='user', password='123456')
        self.wishlist = WishList.objects.create()

    def test_set_and_delete_user_in_wishlist(self):
        self.wishlist.user = self.user
        self.wishlist.save(update_fields=['user'])
        self.assertEqual(self.wishlist.user, self.user)
        self.assertEqual(len(self.user.wishlist.all()), 1)
        self.user.delete()
        self.assertEqual(len(User.objects.all()), 0)
        self.assertEqual(len(WishList.objects.all()), 0)


class CartTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='user', password='123456')
        self.cart = Cart.objects.create(user=self.user)

    def test_is_used_default_value(self):
        self.assertFalse(self.cart.is_used)

    def test_set_and_delete_user_in_wishlist(self):
        self.assertEqual(self.cart.user, self.user)
        self.assertEqual(len(self.user.carts.all()), 1)
        self.user.delete()
        self.assertEqual(len(User.objects.all()), 0)
        self.assertEqual(len(Cart.objects.all()), 0)

    def test_empty_cart_result(self):
        param = ['final_price', 'qty']
        for i in param:
            r = self.cart.get_cart_result(i)
            self.assertEqual(r, 0)

    def test_cart_result_with_product_items(self):
        cart_item = CartItem.objects.create(
            book=Book.objects.create(title='title'),
            qty=1,
            cart=self.cart
        )
        self.assertIn(cart_item, self.cart.cart_items.all())
        self.assertEqual(len(self.cart.cart_items.all()), 1)
        cart_final_price = self.cart.get_cart_result('final_price')
        self.assertEqual(cart_final_price, Decimal('50.00'))
        cart_final_qty = self.cart.get_cart_result('qty')
        self.assertEqual(cart_final_qty, 1)


class CartItemTestCase(TestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title='title',
            info='info',
            price=Decimal(100.00)
        )
        self.user = User.objects.create(username='user', password='123456')
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            book=self.book,
            qty=1,
            cart=self.cart
        )

    def test_set_final_price_on_save(self):
        self.assertEqual(self.cart_item.final_price, Decimal(100.00))
        self.cart_item.qty = 2
        self.cart_item.save(update_fields=['qty'])
        self.assertEqual(self.cart_item.final_price, Decimal(200.00))

    def test_book_on_delete(self):
        self.book.delete()
        self.assertEqual(len(CartItem.objects.all()), 0)

    def test_cart_on_delete(self):
        self.cart.delete()
        self.assertEqual(len(CartItem.objects.all()), 0)

    def test_set_book(self):
        book = Book.objects.create(
            title='another title',
            info='another info'
        )
        self.cart_item.book = book
        self.cart_item.save(update_fields=['book'])
        self.assertIn(self.cart_item, book.cart_items.all())

    def test_set_cart(self):
        cart = Cart.objects.create(user=self.user)
        self.cart_item.cart = cart
        self.cart_item.save(update_fields=['cart'])
        self.assertIn(self.cart_item, cart.cart_items.all())


class UserAccountTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='user', password='123456')
        self.user_acc = UserAccount.objects.create(
            user=self.user
        )

    def test_default_image(self):
        self.assertEqual(self.user_acc.image, 'default_avatar.jpg')

    def test_user_on_delete(self):
        self.assertEqual(self.user, self.user_acc.user)
        self.user.delete()
        self.assertEqual(len(UserAccount.objects.all()), 0)

    def test_set_another_image(self):
        with open('test_images/book1.png', 'rb') as image:
            new_image = File(image)
            self.user_acc.image.save('new_image.png', new_image)
            self.assertEqual(self.user_acc.image.name, 'user/new_image.png')
            os.remove('media/user/new_image.png')
            self.user_acc.image = None
            self.user_acc.save(update_fields=['image'])
            self.assertEqual(self.user_acc.image.name, 'default_avatar.jpg')


class BookTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        MainCategory.objects.create(title='main_category')
        BookCategory.objects.create(title='book_category')
        SpecialCategory.objects.create(title='special_category')

    def setUp(self):
        self.book = Book.objects.create(
            title='title',
            info='info',
            slug='slug'
        )

    def test_set_and_delete_book_category(self):
        book_c = BookCategory.objects.first()
        self.book.bookcategories.add(book_c)
        self.assertIn(book_c, self.book.bookcategories.all())
        self.assertIn(self.book, book_c.books.all())
        self.assertEqual(len(self.book.bookcategories.all()), 1)
        book_c.delete()
        self.assertEqual(len(self.book.bookcategories.all()), 0)

    def test_set_and_delete_special_category(self):
        special_c = SpecialCategory.objects.first()
        self.book.specialcategories.add(special_c)
        self.assertIn(special_c, self.book.specialcategories.all())
        self.assertIn(self.book, special_c.books.all())
        self.assertEqual(len(self.book.specialcategories.all()), 1)
        special_c.delete()
        self.assertEqual(len(self.book.specialcategories.all()), 0)

    def test_set_and_delete_wishlist(self):
        wishlist = WishList.objects.create()
        self.book.wishlist = wishlist
        self.book.save(update_fields=['wishlist'])
        self.assertEqual(self.book.wishlist, wishlist)
        wishlist.delete()
        self.assertIsNone(Book.objects.first().wishlist)

    def test_default_values_in_created_book(self):
        book = Book(
            title='title',
            info='info',
            mark=4
        )
        self.assertEqual(book.price, Decimal(50.00))
        self.assertEqual(book.slug, '')
        book.save()
        self.assertNotEquals(book.slug, '')
        self.assertEqual(book.mark, 0)
        self.assertEqual(book.image.name, 'default_book_image.jpg')

    def test_get_absolute_url(self):
        self.assertEqual(self.book.get_absolute_url(), reverse(
            'book_detail', kwargs={'book_slug': self.book.slug}))

    def test_get_book_count_in_cart(self):
        cart = Cart.objects.create(
            user=User.objects.create(username='user', password='123456')
        )
        self.assertEqual(self.book.get_book_count_in_cart(cart), 0)
        cart_item = CartItem.objects.create(
            book=self.book,
            qty=2,
            cart=cart
        )
        self.assertEqual(self.book.get_book_count_in_cart(cart), 2)

    def test_get_average_book_mark_value(self):
        user_acc = UserAccount.objects.create(
            user=User.objects.create(username='user', password='123456')
        )
        self.assertEqual(self.book.get_average_book_mark_value(), 0)
        marks = [1, 2, 3, 4, 5]
        for i in marks:
            comment = Comment.objects.create(
                book=self.book,
                user_account=user_acc,
                text=f"my mark is: {i}",
                book_mark=i
            )
        self.assertEqual(self.book.get_average_book_mark_value(), 3)
        

class CommentTestCase(TestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title='title',
            info='info',
            slug='slug'
        )
        self.user_account = UserAccount.objects.create(
            user=User.objects.create(username='username', password='123456')
        )


    def test_set_user_account_and_book(self):
        comment = Comment.objects.create(
            book=self.book,
            text='text',
            user_account=self.user_account,
            book_mark=5
        )
        self.assertEqual(len(Comment.objects.all()), 1)
        self.assertEqual(comment.book, self.book)
        self.assertEqual(comment.user_account, self.user_account)
        self.assertIn(comment, self.book.comments.all())
        self.assertIn(comment, self.user_account.comments.all())

        another_book = Book.objects.create(
            title='another title',
            info='another info'
        )
        comment.book = another_book
        comment.save(update_fields=['book'])
        self.assertEqual(comment.book, another_book)

        another_user_account = UserAccount.objects.create(
            user=User.objects.create(username='username1', password='123456')
        )

        comment.user_account = another_user_account
        comment.save(update_fields=['user_account'])
        self.assertEqual(comment.user_account, another_user_account)

    def test_delete_book(self):
        self.book.delete()
        self.assertEqual(len(Comment.objects.all()), 0)

    def test_delete_user_account(self):
        self.user_account.delete()
        self.assertEqual(len(Comment.objects.all()), 0)

    def test_get_background_color(self):
        comment = Comment.objects.create(
            book=self.book,
            text='text',
            user_account=self.user_account,
            book_mark=5
        )
        self.assertEqual(comment.get_background_color(), '110, 219, 77, .5')


class CheckoutTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        Book.objects.create(title='title', price=Decimal('100.00'))
        Book.objects.create(title='title1', price=Decimal('150.00'))
        user = User.objects.create(username='user', password='123456')
        UserAccount.objects.create(user=user)
        Cart.objects.create(user=user) 
        Cart.objects.create(user=user)

    def setUp(self):
        self.cart = Cart.objects.first()
        self.user_account = UserAccount.objects.first()
        self.checkout = Checkout.objects.create(
            cart=self.cart,
            user_account=self.user_account,
            first_name='first_name',
            last_name='last_name',
        )

    def test_get_fullprice(self):
        self.assertEqual(self.checkout.get_fullprice(), 0)
        for i in range(2):
            cart_item = CartItem.objects.create(
                book=Book.objects.get(id=i+1),
                qty=1,
                cart=self.cart
            )
        self.assertEqual(self.checkout.get_fullprice(), Decimal('250.00'))

    def test_set_and_delete_cart(self):
        another_cart = Cart.objects.last()
        self.checkout.cart = another_cart 
        self.checkout.save(update_fields=['cart'])
        self.assertEqual(self.checkout.cart, another_cart)
        self.assertEqual(another_cart.checkout, self.checkout)
        another_cart.delete()
        self.assertEqual(len(Checkout.objects.all()), 0)





