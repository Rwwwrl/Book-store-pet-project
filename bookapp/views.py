from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect, reverse, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.safestring import mark_safe

import json
import sys

from .models import MainCategory, BookCategory, Book, SpecialCategory, WishList, Cart, CartItem, UserAccount
from .forms import UserAccountForm, CheckoutForm, CommentForm, LoginForm, RegistrForm
from .mixins import UserMixin, MyLoginRequiredMixin
from services import services


sys.path.append('..')


class MainPage(UserMixin, ListView):

    template_name = 'bookapp/main_page.html'
    context_object_name = 'books'

    paginate_by = 4

    def dispatch(self, request, *args, **kwargs):
        special_category_slug = kwargs.get('special_category_slug', '')
        services.get_queryset_for_main_page(self, special_category_slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['special_categorys'] = SpecialCategory.objects.all()
        context['is_it_special'] = self.is_it_special
        context['special_category'] = self.special_category
        return context


class BookDetail(UserMixin, DetailView):

    model = Book
    context_object_name = 'book'
    template_name = 'bookapp/book_detail.html'
    slug_url_kwarg = 'book_slug'

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment_model = services.save_comment_and_return_comment_model(self, comment_form)
                return services.json_responce(self, comment_model)
            return comment_form.form_invalid()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.user.is_authenticated:
            context['is_book_on_wishlist'] = services.is_book_on_wishlist(self)
            context['count_in_cart'] = self.object.get_book_count_in_cart(self.cart)
        context['comments'] = services.get_book_comments(self)
        context['comment_form'] = CommentForm()
        context['you_may_also_like_books'] = services.get_also_like_books_queryset(self)
        return context


class BookCategoryDetail(UserMixin, ListView):

    context_object_name = 'books'
    template_name = 'bookapp/bookcategory_books.html'

    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.bookcategory = get_object_or_404(BookCategory, slug=kwargs.get('bookcategory_slug'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self.bookcategory.books.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_title'] = self.bookcategory.title
        return context


class AddToWishList(MyLoginRequiredMixin, UserMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        services.add_book_to_wishlist(self, request, book_slug)
        return redirect('book_detail', book_slug=book_slug)


class DeleteFromWishList(MyLoginRequiredMixin, UserMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug', '')
        services.delete_book_from_wishlist(self, request, book_slug)
        return redirect('wishlist_page')


class AddToCart(MyLoginRequiredMixin, UserMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        services.add_book_to_cart(self, request, book_slug)
        return redirect('book_detail', book_slug=book_slug)


class RemoveFromCart(MyLoginRequiredMixin, UserMixin):

    def get(self, request, *args, **kwargs):
        cart_item_id = kwargs.get('id')
        services.remove_book_from_cart(self, cart_item_id)
        return redirect('cart_page')


class WishListView(MyLoginRequiredMixin, UserMixin, ListView):

    context_object_name = 'books'
    template_name = 'bookapp/account_page/wish_page.html'
    paginate_by = 8

    def get_queryset(self, **kwargs):
        return self.wishlist.books.all().order_by('-id')


class CartView(MyLoginRequiredMixin, UserMixin):

    def get(self, request, *args, **kwargs):
        return render(request, 'bookapp/account_page/cart_page.html', self.get_context_data())

    def post(self, request, *args, **kwargs):
        checkout_form = CheckoutForm(request.POST)
        if checkout_form.is_valid():
            services.save_checkout(self, checkout_form)
            messages.add_message(request, messages.SUCCESS,
                                 'You have succesfully placed an order')
            return redirect('main_page')
        context = self.get_context_data()
        context['checkout_form'] = checkout_form
        return render(request, 'bookapp/account_page/cart_page.html', context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_final_qty'] = self.cart.get_cart_result('qty')
        context['checkout_form'] = CheckoutForm(instance=self.account)
        context['cart_products'] = self.cart.cart_items.all()
        return context


class RecalcCartView(MyLoginRequiredMixin, UserMixin):

    def post(self, request, *args, **kwargs):
        for id in request.POST:
            if not id.startswith('csrf'):
                cart_item = get_object_or_404(self.cart.cart_items, id=id)
                # cart_item = self.cart.cart_items.get(id=id)
                cart_item.qty = int(request.POST[id])
                cart_item.save()
        return redirect('cart_page')


class AccountView(MyLoginRequiredMixin, UserMixin):

    def get(self, request, *args, **kwargs):
        return render(request, 'bookapp/account_page/account_page.html', self.get_context_data())

    def post(self, request, *args, **kwargs):
        form = UserAccountForm(
            request.POST, request.FILES, instance=self.account)
        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Your profile settings saved')
            return redirect('account_page')
        context = self.get_context_data()
        context['form'] = form
        return render(request, 'bookapp/account_page/account_page.html', context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserAccountForm(instance=self.account)
        context['account'] = self.account
        return context


class CheckoutsHistoryView(MyLoginRequiredMixin, UserMixin, ListView):

    template_name = 'bookapp/account_page/checkouts.html'
    context_object_name = 'checkouts'

    def get_queryset(self, *args, **kwargs):
        account = self.user.account
        return account.checkouts.all().order_by('-id')


class BookComments(UserMixin, ListView):

    template_name = 'bookapp/book_comments.html'
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


class SearhView(UserMixin):

    def post(self, request, *args, **kwargs):
        input_data = request.POST.get('search', '').lower()
        category_queryset, book_queryset = services.get_search_results(
            input_data)
        context = self.get_context_data()
        context['categorys'] = category_queryset
        context['books'] = book_queryset
        return render(request, 'bookapp/search_result_page.html', context=context)


class LoginView(View):
    def get(self, request, *args, **kwargs):
        context = {
            'login_form': LoginForm()
        }
        return render(request, 'bookapp/login.html', context)

    def post(self, request, *args, **kwargs):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            message_text = f'Welcome back <span class="username">@username</span>'
            services.authenticate_and_login_user(
                request, username, password, message_text)
            return redirect('main_page')
        context = {
            'login_form': login_form
        }
        return render(request, 'bookapp/login.html', context)


class RegistrationView(View):

    def get(self, request, *args, **kwargs):
        context = {
            'register_form': RegistrForm()
        }
        return render(request, 'bookapp/register_page.html', context)

    def post(self, request, *args, **kwargs):
        register_form = RegistrForm(request.POST)
        if register_form.is_valid():
            user_model = services.register_user(register_form)
            message_text = f'Hello! Ty for registration <span class="username">@{user_model.username}</span>'
            services.authenticate_and_login_user(
                request, user_model.username, register_form.cleaned_data['password'], message_text)
            UserAccount.objects.create(
                user=user_model, email=user_model.email)
            return redirect('main_page')
        context = {
            'register_form': register_form
        }
        return render(request, 'bookapp/register_page.html', context)


def logout_view(request):
    logout(request)
    return redirect('main_page')
