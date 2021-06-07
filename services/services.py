from bookapp.views import *


# MainPage
def get_queryset_for_main_page(instance, slug):
    if slug:
        instance.special_category = get_object_or_404(
            SpecialCategory, slug=slug)
        instance.queryset = instance.special_category.books.all()
        instance.is_it_special = True
    else:
        instance.special_category = None
        instance.queryset = Book.objects.all()
        instance.is_it_special = False


# BookDetail
def save_comment_and_return_comment_model(instance, form):
    comment_model = form.save(commit=False)
    comment_model.user_account = instance.account
    comment_model.book = instance.object
    comment_model.save()
    instance.object.save()
    return comment_model


def json_responce(instance, comment_model):
    url = reverse('book_comments', kwargs={
        'book_slug': comment_model.book.slug})
    return JsonResponse({'good': True, 'comment_info': {
        'profile_image': instance.account.image.url,
        'profile_username': instance.user.username,
        'date_of_creation': comment_model.date_of_creation.strftime('%B %d, %Y'),
        'text': comment_model.text,
        'book_mark': comment_model.book_mark,
        'url': url
    }}, status=200)


def is_book_on_wishlist(instance):
    return instance.wishlist.books.filter(slug=instance.object.slug).exists()


def get_book_comments(instance):
    return instance.object.comments.all().order_by('id')[:5]


def get_also_like_books_queryset(instance):
    if instance.object.bookcategory:
        return instance.object.bookcategory.books.exclude(id=instance.object.id).order_by('-mark')


# AddToWishList
def add_book_to_wishlist(instance, request, slug):
    if not instance.wishlist.books.filter(slug=slug).exists():
        book_model = get_object_or_404(Book, slug=slug)
        instance.wishlist.books.add(book_model)
        messages.add_message(request, messages.SUCCESS, 'Added to wish list')
    else:
        messages.add_message(request, messages.WARNING,
                             'You already added this book to wishlist')


# DeleteFromWishList
def delete_book_from_wishlist(instance, request, slug):
    if instance.wishlist.books.filter(slug=slug).exists():
        book_model = get_object_or_404(Book, slug=slug)
        instance.wishlist.books.remove(book_model)
    else:
        messages.add_message(request, messages.WARNING,
                             'This book isn`t on your wishlist')


# AddToCart
def add_book_to_cart(instance, request, slug):
    book = get_object_or_404(Book, slug=slug)
    if not instance.cart.cart_items.filter(book=book).exists():
        cart_item = CartItem.objects.create(
            book=book, qty=1, cart=instance.cart
        )
        messages.add_message(request, messages.SUCCESS,
                             'Book added to cart')
    else:
        cart_item = instance.cart.cart_items.get(book=book)
        cart_item.qty += 1
        cart_item.save()
        messages.add_message(
            request, messages.INFO, 'The cart already contains this book, the qty has been increased by 1')


# RemoveFromCart
def remove_book_from_cart(instance, cart_item_id):
    if instance.cart.cart_items.filter(id=cart_item_id).exists():
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        cart_item.delete()


# CartView
def save_checkout(instance, form):
    checkout_model = form.save(commit=False)
    checkout_model.cart = instance.cart
    checkout_model.user_account = instance.account
    checkout_model.save()
    instance.cart.is_used = True
    instance.cart.save()


# SearchView
def get_filter_by_slug_or_title_queryset(manager, date):
    return list(manager.filter(Q(title__icontains=date) | Q(slug__icontains=date)))


def get_search_results(data):
    bookcategory_queryset = get_filter_by_slug_or_title_queryset(
        BookCategory.objects, data)
    special_category_queryset = get_filter_by_slug_or_title_queryset(
        SpecialCategory.objects, data)
    book_queryset = get_filter_by_slug_or_title_queryset(
        Book.objects, data)
    category_queryset = bookcategory_queryset + special_category_queryset
    return [category_queryset, book_queryset]


# LoginView
def authenticate_and_login_user(request, username, password, message_text):
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        messages.add_message(request, messages.SUCCESS,
                             mark_safe(message_text))


# RegistrationView
def register_user(form):
    user_model = form.save(commit=False)
    user_model.set_password(form.cleaned_data['password'])
    user_model.save()
    return user_model
