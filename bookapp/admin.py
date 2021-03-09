from django.contrib import admin

# Register your models here.
from .models import MainCategory, UnderCategory, Book

class ModelWithoutSlugAdmin(admin.ModelAdmin):
    exclude = ['slug', ]
    model = None

class MainCategoryAdmin(ModelWithoutSlugAdmin):
    model = MainCategory


class UnderCategoryAdmin(ModelWithoutSlugAdmin):
    model = UnderCategory


class BookAdmin(ModelWithoutSlugAdmin):
    model = Book

# admin.site.register(MainCategory, MainCategoryAdmin)
# admin.site.register(UnderCategory, UnderCategoryAdmin)
# admin.site.register(Book, BookAdmin)

admin.site.register(MainCategory),
admin.site.register(UnderCategory),
admin.site.register(Book),
