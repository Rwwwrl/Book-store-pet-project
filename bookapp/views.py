from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout

from .models import MainCategory, UnderCategory, Book, SpecialCategory, WishList, Cart, ProductItem, UserAccount
from .forms import UserAccountForm, CheckoutForm, CommentaryForm, LoginForm, RegistrForm
from .mixins import UserWishListMixin, MyLoginRequiredMixin


import json


class MainPage(UserWishListMixin, ListView):

    template_name = 'bookapp/main_page.html'
    context_object_name = 'books'

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
                mark = comment_model.book_mark
                self.object.mark += mark
                self.object.save()
                url = reverse('book_comments', kwargs={
                              'book_slug': comment_model.book.slug})
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

    def get_comment_order_by_id(self):
        return self.object.comments.all().order_by('id')[:5]

    def get_also_like_books_queryset(self):
        return self.object.under_category.book.exclude(id=self.object.id).order_by('-mark')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.user.is_authenticated:
            context['is_book_on_wish_list'] = self.is_book_on_wish_list()
            context['count_in_cart'] = self.object.get_book_count_in_cart(
                self.cart)
        context['comments'] = self.get_comment_order_by_id() 
        context['comment_form'] = CommentaryForm()
        context['you_may_also_like_books'] = self.get_also_like_books_queryset()
        return context


class UnderCategoryBooks(UserWishListMixin, ListView):

    context_object_name = 'books'
    template_name = 'bookapp/under_category_books.html'

    paginate_by = 8

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


class AddToWishList(MyLoginRequiredMixin, UserWishListMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug')
        if not self.wishlist.books.filter(slug=book_slug).exists():
            book_model = Book.objects.get(slug=book_slug)
            self.wishlist.books.add(book_model)
        return redirect('book_detail', book_slug=book_slug)


class DeleteFromWishList(MyLoginRequiredMixin, UserWishListMixin):

    def get(self, request, *args, **kwargs):
        book_slug = kwargs.get('book_slug', '')
        if self.wishlist.books.filter(slug=book_slug).exists():
            book_model = Book.objects.get(slug=book_slug)
            self.wishlist.books.remove(book_model)
        return redirect('wish_page')


class AddToCart(MyLoginRequiredMixin, UserWishListMixin):

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


class RemoveFromCart(MyLoginRequiredMixin, UserWishListMixin):

    def get(self, request, *args, **kwargs):
        pi_id = kwargs.get('id')
        if self.cart.product_items.filter(id=pi_id).exists():
            pi = ProductItem.objects.get(id=pi_id)
            pi.delete()
        return redirect('cart_page')


class WishListView(MyLoginRequiredMixin, UserWishListMixin, ListView):

    context_object_name = 'books'
    template_name = 'bookapp/account_page/wish_cart_page.html'
    paginate_by = 8

    def get_queryset(self, **kwargs):
        return self.wishlist.books.all()


class CartView(MyLoginRequiredMixin, UserWishListMixin):


    def get(self, request, *args, **kwargs):
        return render(request, 'bookapp/account_page/cart_page.html', self.get_context_data())

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
        context = self.get_context_data()
        context['checkout_form'] = checkout_form 
        return render(request, 'bookapp/account_page/cart_page.html', context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_final_qty'] = self.cart.get_final_param('qty')
        context['checkout_form'] = CheckoutForm(instance=self.account)
        context['cart_products'] = self.cart.product_items.all()
        return context


class RecalcCartView(MyLoginRequiredMixin, UserWishListMixin):

    def post(self, request, *args, **kwargs):
        for id in request.POST:
            if not id.startswith('csrf'):
                product_item = self.cart.product_items.get(id=id)
                product_item.qty = int(request.POST[id])
                product_item.save()
        return redirect('cart_page')


class MyAccountView(MyLoginRequiredMixin, UserWishListMixin):

    def get(self, request, *args, **kwargs):
        return render(request, 'bookapp/account_page/my_account_page.html', self.get_context_data())

    def post(self, request, *args, **kwargs):
        form = UserAccountForm(
            request.POST, request.FILES, instance=self.account)
        if form.is_valid():
            model = form.save(commit=False)
            model.save()
            return redirect('my_account_page')
        context = self.get_context_data()
        context['form'] = form
        return render(request, 'bookapp/account_page/my_account_page.html', context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserAccountForm(instance=self.account)
        context['account'] = self.account
        return context


class CheckoutsView(MyLoginRequiredMixin, UserWishListMixin, ListView):

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


class SearhView(UserWishListMixin):

    @staticmethod
    def get_filter_by_slug_or_title_queryset(manager, date):
        return list(manager.filter(Q(title__icontains=date) | Q(slug__icontains=date)))

    def post(self, request, *args, **kwargs):
        date = request.POST.get('search', '').lower()
        under_category_queryset = self.get_filter_by_slug_or_title_queryset(
            UnderCategory.objects, date)
        special_category_queryset = self.get_filter_by_slug_or_title_queryset(
            SpecialCategory.objects, date)
        book_category_queryset = self.get_filter_by_slug_or_title_queryset(Book.objects, date)
        under_category_queryset.extend(special_category_queryset)
        context = self.get_context_data()
        context['categorys'] = under_category_queryset
        context['books'] = book_category_queryset
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
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('main_page')
        context = {
            'login_form': login_form    
        }
        return render(request, 'bookapp/login.html', context)


class RegistrView(View):

    def get(self, request, *args, **kwargs):
        context = {
            'register_form': RegistrForm()
        }
        return render(request, 'bookapp/register_page.html', context)

    def post(self, request, *args, **kwargs):
        register_form = RegistrForm(request.POST)
        if register_form.is_valid():
            user_model = register_form.save(commit=False)
            user_model.set_password(register_form.cleaned_data['password'])
            user_model.save()
            user = authenticate(username=user_model.username, password=register_form.cleaned_data['password'])
            if user:
                login(request, user)
                UserAccount.objects.create(user=user_model, email=user_model.email) 
                return redirect('main_page')
        context = {
            'register_form': register_form
        }
        return render(request, 'bookapp/register_page.html', context)

def logout_view(request):
    logout(request)
    return redirect('main_page')
































