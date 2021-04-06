from django.views import View
from django.views.generic.base import ContextMixin

from .models import MainCategory, BookCategory, Book, SpecialCategory, WishList, Cart, UserAccount
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin


class UserWishListMixin(ContextMixin, View):

    def dispatch(self, request, *args, **kwargs):
        # get user model
        self.user = request.user
        # get his wishlist
        if self.user.is_authenticated:
            self.wishlist, wishlist_created = WishList.objects.get_or_create(
                user=self.user
            )
            # get his cart
            self.cart, cart_created = Cart.objects.get_or_create(
                user=self.user, is_used=False
            )
            # get his account
            self.account, account_created = UserAccount.objects.get_or_create(
                user=self.user
            )
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['main_categorys'] = MainCategory.objects.all()
        if self.user.is_authenticated:
            context['wishlist'] = self.wishlist.books.all()
            context['cart'] = self.cart.cart_items.all()
            context['cart_final_price'] = self.cart.get_final_param('final_price')
        return context
    

class MyLoginRequiredMixin(LoginRequiredMixin):

    login_url = settings.LOGIN_URL

