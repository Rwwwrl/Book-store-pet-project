from django.urls import path

from .views import MainPage, BookDetail, UnderCategoryBooks, AddToWishList, AddToCart, WishListView, CartView, RecalcCartView, MyAccountView

urlpatterns = [
    path('main-page/', MainPage.as_view(), name='main_page'),
    path('main_page/<str:special_category_slug>/', MainPage.as_view(), name='main_page_with_special'),
    path('main-page/books/<str:book_slug>/', BookDetail.as_view(), name='book_detail'),
    path('main-page/<str:under_category_slug>/', UnderCategoryBooks.as_view(), name='undercategory_books'),
    path('add_to_wish/<str:book_slug>/', AddToWishList.as_view(), name='add_to_wish'),
    path('add_to_cart/<str:book_slug>/', AddToCart.as_view(), name='add_to_cart'),
    path('account_page/my_account/', MyAccountView.as_view(), name='my_account_page'),
    path('account_page/wish_list/', WishListView.as_view(), name='wish_page'),
    path('account_page/cart_page/', CartView.as_view(), name='cart_page'),
    path('account_page/cart_page/recalt_cart/', RecalcCartView.as_view(), name='recalc_cart')

]
