from django.urls import path, include
from . import views

app_name = 'pdf_processor'

urlpatterns = [
    path('', views.home_redirect_view, name='home'),  # <-- nueva línea
    path('upload/', views.upload_pdf_view, name='upload_pdf'),
    path('products/', views.product_list_view, name='product_list'),
    path('reporte-semanal/', views.weekly_price_report, name='weekly_report'),
]