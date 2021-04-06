from django.urls import path

from .views import *

urlpatterns = [
    path('main-page/', MainPage.as_view(), name='main_page'),
    path('main_page/<str:special_category_slug>/', MainPage.as_view(), name='special_category_page'),
    path('main-page/books/<str:book_slug>/', BookDetail.as_view(), name='book_detail'),
    path('main-page/<str:bookcategory_slug>/', BookCategoryBooks.as_view(), name='bookcategory_page'),
    path('add_to_wish/<str:book_slug>/', AddToWishList.as_view(), name='add_to_wish'),
    path('delete_from_wish/<str:book_slug>', DeleteFromWishList.as_view(), name='delete_from_wish'),
    path('add_to_cart/<str:book_slug>/', AddToCart.as_view(), name='add_to_cart'),
    path('remove_from_cart/<int:id>', RemoveFromCart.as_view(), name='remove_from_cart'),
    path('account_page/account/', MyAccountView.as_view(), name='account_page'),
    path('account_page/wishlist/', WishListView.as_view(), name='wishlist_page'),
    path('account_page/cart_page/', CartView.as_view(), name='cart_page'),
    path('account_page/checkout_history/', CheckoutsView.as_view(), name='checkouts_page'), 
    path('account_page/cart_page/recalt_cart/', RecalcCartView.as_view(), name='recalc_cart'),
    path('<str:book_slug>/comments/', BookComments.as_view(), name='book_comments'),
    path('search_result/', SearhView.as_view(), name='search'),

    path('login/', LoginView.as_view(), name='login'),
    path('registration/', RegistrView.as_view(), name='registration'),
    path('logout/', logout_view, name='logout'),
]
