from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect, reverse
from django.http import JsonResponse

from .models import MainCategory, UnderCategory, Book, SpecialCategory, WishList, Cart, ProductItem
from .forms import UserAccountForm, CheckoutForm, CommentaryForm
from .mixins import UserWishListMixin

import json


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

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            comment_form = CommentaryForm(request.POST)
            if comment_form.is_valid():
                comment_model = comment_form.save(commit=False)
                comment_model.user_account = self.account
                comment_model.book = self.object
                comment_model.save()
                url = reverse('book_comments', kwargs={'book_slug': comment_model.book.slug})
                return JsonResponse({'good': True, 'comment_info': {
                    'profile_image': self.account.image.url, 
                    'profile_first_name': self.account.first_name,
                    'date_of_created': comment_model.date_of_created.strftime('%B %d, %Y'),
                    'text': comment_model.text,
                    'book_mark': comment_model.book_mark,
                    'url': url
                    }}, status=200)
            return comment_form.form_invalid()

    def is_book_on_wish_list(self):
        return self.wishlist.books.filter(slug=self.object.slug).exists()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_book_on_wish_list'] = self.is_book_on_wish_list()
        context['count_in_cart'] = self.object.get_book_count_in_cart(
            self.cart)
        context['comments'] = self.object.comments.all().order_by('id')[:5]
        context['comment_form'] = CommentaryForm()
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
        return redirect('book_detail', book_slug=book_slug)


class DeleteFromWishList(UserWishListMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug', '')
        if self.wishlist.books.filter(slug=book_slug).exists():
            book_model = Book.objects.filter(slug=book_slug)[0]
            self.wishlist.books.remove(book_model)
        return redirect('wish_page')


class AddToCart(UserWishListMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        book = Book.objects.get(slug=book_slug)
        if not self.cart.product_items.filter(book=book).exists():
            product_item = ProductItem.objects.create(
                book=book, qty=1, cart=self.cart
            )
        else:
            product_item = self.cart.product_items.get(book=book)
            product_item.qty += 1
            product_item.save()
        return redirect('book_detail', book_slug=book_slug)


class RemoveFromCart(UserWishListMixin):

    def get(self, request, *args, **kwargs):
        pi_id = kwargs.get('id')
        if self.cart.product_items.filter(id=pi_id).exists():
            pi = ProductItem.objects.get(id=pi_id)
            pi.delete()
        return redirect('cart_page')


class WishListView(UserWishListMixin, ListView):

    context_object_name = 'books'
    template_name = 'bookapp/account_page/wish_cart_page.html'
    paginate_by = 8

    def get_queryset(self, **kwargs):
        return self.wishlist.books.all()


class CartView(UserWishListMixin, ListView):

    context_object_name = 'cart_products'
    template_name = 'bookapp/account_page/cart_page.html'

    def post(self, request, *args, **kwargs):
        print('this is post')

    def get_queryset(self, **kwargs):
        return self.cart.product_items.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_final_qty'] = self.cart.get_final_param('qty')
        context['checkout_form'] = CheckoutForm(instance=self.account)
        return context


class RecalcCartView(UserWishListMixin):

    def post(self, request, *args, **kwargs):
        for id in request.POST:
            if not id.startswith('csrf'):
                product_item = self.cart.product_items.get(id=id)
                product_item.qty = int(request.POST[id])
                product_item.save()
        return redirect('cart_page')


class MyAccountView(UserWishListMixin):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if hasattr(self.account, 'image'):
            context['account_image'] = self.account.image
        return render(request, 'bookapp/account_page/my_account_page.html', context)

    def post(self, request, *args, **kwargs):
        form = UserAccountForm(
            request.POST, request.FILES, instance=self.account)
        if form.is_valid():
            form.save()
            return redirect('my_account_page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserAccountForm(instance=self.account)
        return context


class CheckoutView(UserWishListMixin):

    def post(self, request, *args, **kwargs):
        checkout_form = CheckoutForm(request.POST)

        if checkout_form.is_valid():
            checkout_model = checkout_form.save(commit=False)
            checkout_model.cart = self.cart
            checkout_model.user_account = self.account
            checkout_model.save()
            self.cart.is_used = True
            self.cart.save()
        return redirect('main_page')


class CheckoutsView(UserWishListMixin, ListView):

    template_name = 'bookapp/account_page/checkouts.html'
    context_object_name = 'checkouts'

    def get_queryset(self, *args, **kwargs):
        account = self.user.account
        return account.checkouts.all().order_by('-id')


class BookComments(UserWishListMixin, ListView):

    template_name = 'bookapp/all_comments.html'
    context_object_name = 'comments'

    paginate_by = 5

    def dispatch(self, *args, **kwargs):
        self.book = Book.objects.get(slug=kwargs.get('book_slug'))
        self.comments = self.book.comments.all()
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.book
        return context

    def get_queryset(self, **kwargs):
        return self.comments
