from django.urls import path, include
from .views import IndexView, RegisterView, custom_login_view, LogoutView

urlpatterns = [
    path('', IndexView.as_view(), name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', custom_login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]