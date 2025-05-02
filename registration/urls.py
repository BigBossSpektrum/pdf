from django.urls import path, include
from .views import IndexView, RegisterView, CustomLoginView, LogoutView

urlpatterns = [
    path('', IndexView.as_view(), name='dashboard'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]