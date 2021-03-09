from django.shortcuts import redirect


def redirect_to_main_page(request):
    return redirect('/main-page/')