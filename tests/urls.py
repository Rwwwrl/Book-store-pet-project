from django.urls import path

from .views import UserMixinChild

app_name = 'tests'
urlpatterns = [
    path('user-mixin-test/', UserMixinChild.as_view(), name='user-mixin-test')
]







