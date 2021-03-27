from django.views import View
from django.views.generic.base import ContextMixin

from .models import MainCategory, UnderCategory, Book, SpecialCategory, WishList, Cart, UserAccount

class UserWishListMixin(ContextMixin, View):

    def dispatch(self, request, *args, **kwargs):
        # get user model
        self.user = request.user
        # get his wishlist
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
        context['wishlist'] = self.wishlist.books.all()
        context['cart'] = self.cart.product_items.all()
        context['cart_final_price'] = self.cart.get_final_param('final_price')
        return context
    



