from django.contrib import admin

# Register your models here.
from .models import MainCategory, UnderCategory, SpecialCategory, Book, WishList, UserAccount

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
admin.site.register(SpecialCategory),
admin.site.register(WishList),
admin.site.register(UserAccount),