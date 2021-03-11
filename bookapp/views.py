from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from .models import MainCategory, UnderCategory, Book


class MainPage(ListView):

    # model = MainCategory - сокращенная запись queryset = MainCategory.objects.all
    model = Book
    template_name = 'bookapp/main_page.html'
    context_object_name = 'books'

    # пагинация
    paginate_by = 4

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['main_categorys'] = MainCategory.objects.all()
        return context


class BookDetail(DetailView):

    model = Book
    context_object_name = 'book'
    template_name = 'bookapp/book_detail.html'
    slug_url_kwarg = 'book_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['main_categorys'] = MainCategory.objects.all()
        return context

class BookList(ListView):

    context_object_name = 'books'
    template_name = 'bookapp/book_list.html'

    paginate_by = 4

    def dispatch(self, request, *args, **kwargs):
        self.under_category = UnderCategory.objects.filter(slug=kwargs.get('under_category_slug'))[0]
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self.under_category.book.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['main_categorys'] = MainCategory.objects.all()
        context['category_title'] = self.under_category.title
        return context
