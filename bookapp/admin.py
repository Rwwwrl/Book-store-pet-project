from django.contrib import admin

# Register your models here.
from .models import MainCategory, BookCategory, SpecialCategory, Book, WishList, UserAccount, CartItem, Checkout, Cart, Comment


class ModelWithoutSlugAdmin(admin.ModelAdmin):
    exclude = ['slug', ]
    model = None


class MainCategoryAdmin(ModelWithoutSlugAdmin):
    model = MainCategory


class BookCategoryAdmin(ModelWithoutSlugAdmin):
    model = BookCategory


class SpecialCategoryAdmin(ModelWithoutSlugAdmin):
    model = SpecialCategory


class CommentInline(admin.TabularInline):
    model = Comment


class BookAdmin(admin.ModelAdmin):
    model = Book
    exclude = ['slug', 'mark', 'wishlist', ]
    inlines = [CommentInline, ]


class CartItemInline(admin.TabularInline):
    model = CartItem


class CartAdmin(admin.ModelAdmin):
    model = Cart
    fields = ['user', 'is_used']
    inlines = [CartItemInline, ]


admin.site.register(MainCategory, MainCategoryAdmin),
admin.site.register(BookCategory, BookCategoryAdmin),
admin.site.register(SpecialCategory, SpecialCategoryAdmin),
admin.site.register(Book, BookAdmin),
admin.site.register(Cart, CartAdmin),
admin.site.register(WishList),
admin.site.register(UserAccount),
admin.site.register(CartItem),
admin.site.register(Checkout),
admin.site.register(Comment)
