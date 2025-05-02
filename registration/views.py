from django.views import View
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .forms import CustomUserCreationForm

class IndexView(LoginRequiredMixin, View):
    login_url = 'login'  # nombre de la URL de login
    redirect_field_name = 'next'

    def get(self, request):
        return render(request, 'base.html')

class RegisterView(View):

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')  # o la vista principal que uses
        form = CustomUserCreationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        return render(request, 'register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('dashboard')

class LogoutView(View):
    def get(self, request):
        logout(request)  # Realiza el logout y limpia la sesión

        # Limpiar cookies de sesión de forma explícita (por si no se hace correctamente)
        response = HttpResponseRedirect(reverse_lazy('login'))
        response.delete_cookie('sessionid')  # Borra la cookie de sesión
        return response