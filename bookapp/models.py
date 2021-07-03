from django.db import models
from django.db.models import Sum
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from random import random

User = get_user_model()


def create_slug(title):
    slug = str(slugify(title)) + '-' + str(int(random() * 100000))
    return slug


class Category(models.Model):
    """ Абстрактный класс категории для унаследования """

    class Meta:
        abstract = True

    title = models.CharField(max_length=30)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.title)
        super().save(*args, **kwargs)


class SpecialCategory(Category):
    """ Специальная категория, например: "Распродажа",  "Хиты продаж" """

    def get_absolute_url(self):
        return reverse('special_category_page', kwargs={'special_category_slug': self.slug})


class MainCategory(Category):
    """ Главная, общая категория, например: "Детективы" """

    pass


class BookCategory(Category):
    """ Подкатегория, к которой относится сама книга, например: "Детские детективы" """

    main_category = models.ForeignKey(
        MainCategory, related_name='bookcategories', on_delete=models.CASCADE, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('bookcategory_page', kwargs={'bookcategory_slug': self.slug})

    def get_books_count(self):
        return len(self.books.all())


class WishList(models.Model):
    """ Список отложенных пользователем книг """

    user = models.ForeignKey(User, related_name='wishlist',
                             on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'WishList: {self.user.username}, {self.id}'


class Book(models.Model):
    """ Модель Книги """

    title = models.CharField(max_length=40)
    image = models.ImageField(default='default_book_image.jpg')
    slug = models.SlugField(unique=True, blank=True)
    info = models.TextField(max_length=300)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    mark = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True, default=0)

    bookcategories = models.ManyToManyField(
        BookCategory, related_name='books', blank=True)
    specialcategories = models.ManyToManyField(
        SpecialCategory, related_name='books', blank=True)
    wishlist = models.ForeignKey(
        WishList, related_name='books', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.title)
        if not self.image:
            self.image = "default_book_image.jpg"
        if self.comments.all().exists():
            self.mark = self.get_average_book_mark_value()
        else:
            self.mark = 0
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('book_detail', kwargs={'book_slug': self.slug})

    def get_book_count_in_cart(self, cart):
        queryset = cart.cart_items.filter(book__slug=self.slug)
        if queryset.exists():
            return queryset[0].qty
        return 0

    def get_average_book_mark_value(self):
        if not self.comments.all().exists():
            return 0
        sum_of_comment_mark = sum(
            [comment.book_mark for comment in self.comments.all()])
        average_value = sum_of_comment_mark / len(self.comments.all())
        return average_value

    def __str__(self):
        return self.title


class Cart(models.Model):
    """ Модель корзины пользователя """

    user = models.ForeignKey(User, related_name='carts',
                             on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username}`s cart, is_used = {self.is_used}'

    def get_cart_result(self, param):
        if not self.cart_items.exists():
            return 0
        final_param = self.cart_items.aggregate(Sum(param))
        return round(final_param[param+'__sum'], 2)


class CartItem(models.Model):
    """ Модель товара в корзине """

    book = models.ForeignKey(
        Book, related_name='cart_items', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    cart = models.ForeignKey(
        Cart, related_name='cart_items', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.book.title

    def save(self, *args, **kwargs):
        self.final_price = self.book.price * self.qty
        super().save(*args, **kwargs)


class UserAccount(models.Model):
    """ Аккаунт пользователя """

    user = models.OneToOneField(
        User, related_name='account', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="user/", null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username}'

    def save(self, *args, **kwargs):
        if not self.image:
            self.image = 'default_avatar.jpg'
        super().save(*args, **kwargs)


class Checkout(models.Model):
    """ Модель заказа """

    cart = models.OneToOneField(
        Cart, related_name='checkout', on_delete=models.CASCADE)
    user_account = models.ForeignKey(
        UserAccount, related_name='checkouts', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(null=True)
    address = models.CharField(max_length=255, null=True)
    comment = models.TextField(max_length=255, blank=True, null=True)
    delivery_date = models.DateField(null=True)
    date_of_creation = models.DateField(
        auto_now_add=True, blank=True, null=True)
    date_of_change = models.DateField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f'{self.user_account.first_name}`s checkout'

    def get_fullprice(self):
        return self.cart.get_cart_result('final_price')


class Comment(models.Model):
    """ Модель комментария к книгe """

    book = models.ForeignKey(
        Book, related_name='comments', on_delete=models.CASCADE)
    user_account = models.ForeignKey(
        UserAccount, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField(max_length=255, blank=False)
    date_of_creation = models.DateField(
        auto_now_add=True, blank=True, null=True)
    book_mark = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.user_account.user.username}`s comment on {self.book.title} book'

    def get_background_color(self):
        mark_to_bg = {
            1: '173, 41, 31, .5',
            2: '227, 102, 93, .5',
            3: '227, 188, 98, .5',
            4: '175, 214, 103, .5',
            5: '110, 219, 77, .5',
        }
        return mark_to_bg[self.book_mark]
