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
    """ Special category like 'discount', 'special offers' """

    def get_absolute_url(self):
        return reverse('main_page_with_special', kwargs={'special_category_slug': self.slug})


class MainCategory(Category):
    pass


class UnderCategory(Category):
    main_category = models.ForeignKey(
        MainCategory, related_name='under_category', on_delete=models.CASCADE, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('undercategory_books', kwargs={'under_category_slug': self.slug})

    def get_books_count(self):
        return len(self.book.all())


class WishList(models.Model):
    user = models.ForeignKey(User, related_name='wish_list',
                             on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'WishList: {self.user.username}, {self.id}'


class Book(models.Model):
    title = models.CharField(max_length=40)
    image = models.ImageField(default='../media/default.png')
    slug = models.SlugField(unique=True, blank=True)
    info = models.TextField(max_length=300)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)

    under_category = models.ForeignKey(
        UnderCategory, related_name='book', on_delete=models.CASCADE, null=True, blank=True)
    special_category = models.ForeignKey(
        SpecialCategory, related_name='book', on_delete=models.CASCADE, null=True, blank=True)
    wish_list = models.ForeignKey(
        WishList, related_name='books', on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_slug(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('book_detail', kwargs={'book_slug': self.slug})

    def get_book_count_in_cart(self, cart):
        queryset = cart.product_items.filter(book__slug=self.slug)
        if queryset.exists():
            return queryset[0].qty
        return 0

    def __str__(self):
        return self.title


class Cart(models.Model):
    user = models.ForeignKey(User, related_name='cart',
                             on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username}`s cart, is_used = {self.is_used}'

    def get_final_param(self, param):
        if not self.product_items.exists():
            return 0
        final_param = self.product_items.aggregate(Sum(param))
        return final_param[param+'__sum']


class ProductItem(models.Model):
    book = models.ForeignKey(
        Book, related_name='product_item', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    final_price = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    cart = models.ForeignKey(
        Cart, related_name='product_items', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.book.title

    def save(self, *args, **kwargs):
        self.final_price = self.book.price * self.qty
        super().save(*args, **kwargs)


class UserAccount(models.Model):
    user = models.OneToOneField(
        User, related_name='account', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="user/", null=True,
                              blank=True, default='../static/images/default_avatar.jpg')
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Checkout(models.Model):
    cart = models.OneToOneField(
        Cart, related_name='checkout', on_delete=models.CASCADE)
    user_account = models.ForeignKey(
        UserAccount, related_name='checkouts', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(null=True)
    address = models.CharField(max_length=255)
    commentary = models.TextField(max_length=255, blank=True, null=True)
    delivery_date = models.DateField(null=True)
    date_of_created = models.DateField(
        auto_now_add=True, blank=True, null=True)
    date_of_changes = models.DateField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f'{self.user_account.first_name}`s checkout'

    def get_fullprice(self):
        return self.cart.get_final_param('final_price')


class Commentary(models.Model):
    book = models.ForeignKey(
        Book, related_name='comments', on_delete=models.CASCADE)
    user_account = models.ForeignKey(
        UserAccount, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField(max_length=255, blank=False)
    date_of_created = models.DateField(
        auto_now_add=True, blank=True, null=True)
    book_mark = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user_account.first_name}`s comment on {self.book.title} book'

    def get_self_bg_color(self):
        mark_to_bg = {
            1: '173, 41, 31, .5',
            2: '227, 102, 93, .5',
            3: '227, 188, 98, .5',
            4: '175, 214, 103, .5',
            5: '110, 219, 77, .5',
        }
        return mark_to_bg[self.book_mark] 
