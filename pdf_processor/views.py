import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import UploadPDFForm
from .models import Product
from .utils import extract_text_from_pdf, parse_products
from django.db.models import Avg
from django.db.models.functions import TruncWeek
from .models import Product

def home_redirect_view(request):
    return redirect('pdf_processor:upload_pdf')

def export_products_excel(request):
    products = Product.objects.all().values()
    df = pd.DataFrame(products)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=productos.xlsx'
    df.to_excel(response, index=False)
    return response


def upload_pdf_view(request):
    if request.method == 'POST':
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data['pdf_file']
            text = extract_text_from_pdf(pdf_file)
            products = parse_products(text)

            for item in products:
                Product.objects.create(**item)

            return redirect('pdf_processor:product_list')
        form = UploadPDFForm()

    return render(request, 'upload_pdf.html', {'form': form})


def product_list_view(request):
    products = Product.objects.all().order_by('-uploaded_at')
    return render(request, 'list_product.html', {'products': products})

def weekly_price_report(request):
    weekly_data = (
        Product.objects
        .annotate(week=TruncWeek('uploaded_at'))
        .values('name', 'week')
        .annotate(avg_price=Avg('price'))
        .order_by('name', 'week')
    )
    return render(request, 'processor/weekly_report.html', {'weekly_data': weekly_data})