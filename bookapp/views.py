from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect

from .models import MainCategory, UnderCategory, Book, SpecialCategory, WishList, Cart, ProductItem
from .mixins import UserWishListMixin


class MainPage(UserWishListMixin, ListView):

    # model = MainCategory - сокращенная запись queryset = MainCategory.objects.all
    template_name = 'bookapp/main_page.html'
    context_object_name = 'books'

    # пагинация
    paginate_by = 4

    def dispatch(self, request, *args, **kwargs):
        special_category_slug = kwargs.get('special_category_slug', '')
        if special_category_slug:
            self.special_category = SpecialCategory.objects.get(
                slug=special_category_slug)
            self.queryset = self.special_category.book.all()
            self.is_it_special = True
        else:
            self.special_category = None
            self.queryset = Book.objects.all()
            self.is_it_special = False
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['special_categorys'] = SpecialCategory.objects.all()
        context['is_it_special'] = self.is_it_special
        context['special_category'] = self.special_category
        return context


class BookDetail(UserWishListMixin, DetailView):

    model = Book
    context_object_name = 'book'
    template_name = 'bookapp/book_detail.html'
    slug_url_kwarg = 'book_slug'

    def is_book_on_wish_list(self):
        return self.wishlist.books.filter(slug=self.object.slug).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_book_on_wish_list'] = self.is_book_on_wish_list()
        return context


class UnderCategoryBooks(UserWishListMixin, ListView):

    context_object_name = 'books'
    template_name = 'bookapp/under_category_books.html'

    paginate_by = 4

    def dispatch(self, request, *args, **kwargs):
        self.under_category = UnderCategory.objects.get(
            slug=kwargs.get('under_category_slug'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self.under_category.book.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_title'] = self.under_category.title
        return context


class AddToWishList(UserWishListMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug', '')
        if not self.wishlist.books.filter(slug=book_slug).exists():
            book_model = Book.objects.filter(slug=book_slug)[0]
            self.wishlist.books.add(book_model)
        return redirect('main_page')


class AddToCart(UserWishListMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        book = Book.objects.get(slug=book_slug)
        if not self.cart.product_items.filter(book=book).exists():
            product_item = ProductItem.objects.create(
                book=book, qty=1, cart=self.cart
            )
        else:
            product_item = ProductItem.objects.get(book=book)
            product_item.qty += 1
            product_item.save()
        return redirect('main_page')


class WishListView(UserWishListMixin, ListView):

    context_object_name = 'books'
    template_name = 'bookapp/account_page/wish_cart_page.html'
    paginate_by = 8

    def get_queryset(self, **kwargs):
        return self.wishlist.books.all()


class CartView(UserWishListMixin, ListView):

    context_object_name = 'cart_products'
    template_name = 'bookapp/account_page/cart_page.html'

    def get_queryset(self, **kwargs):
        return self.cart.product_items.all()
