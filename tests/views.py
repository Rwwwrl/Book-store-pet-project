from django.views.generic import TemplateView

import sys
sys.path.append('..')

from bookapp.mixins import UserMixin


class UserMixinChild(UserMixin, TemplateView):

    template_name = 'tests/userMixinChild.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.user.is_authenticated:
            context['wishlist_from_dispatch'] = self.wishlist
            context['cart_from_dispatch'] = self.cart
            context['account_from_dispatch'] = self.account
        return context








