from django.urls import path

from .views import MainPage, BookDetail, BookList

urlpatterns = [
    path('main-page/', MainPage.as_view(), name='main_page'),
    path('main-page/books/<str:book_slug>/', BookDetail.as_view(), name='book_detail'),
    path('main-page/<str:under_category_slug>/', BookList.as_view(), name='undercategory_books'),
]
