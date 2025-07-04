from .models import Product, ProcessedPDF
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
    """Redirige a la vista de carga de PDF como página principal."""
    return redirect('pdf_processor:upload_pdf')

def export_products_excel(request):
    """Exporta todos los productos a un archivo Excel descargable."""
    products = Product.objects.all().values()
    if not products:
        return HttpResponse('No hay productos para exportar.', content_type='text/plain')
    df = pd.DataFrame(products)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=productos.xlsx'
    df.to_excel(response, index=False)
    return response


def upload_pdf_view(request):
    """Permite la carga y procesamiento de uno o varios archivos PDF para extraer productos y registrar los PDFs subidos."""
    from django import forms

    # No se puede usar FileField para múltiples archivos en Django Forms estándar.
    # Usamos un formulario vacío y validamos en la vista.
    class MultiPDFUploadForm(forms.Form):
        pass

    # Permitir múltiples archivos desde el request, pero el campo es single en el form

    if request.method == 'POST':
        form = MultiPDFUploadForm(request.POST, request.FILES)
        files = request.FILES.getlist('pdf_file')
        if not files:
            form.add_error(None, 'Debes seleccionar al menos un archivo PDF.')
        else:
            total_nuevos = 0
            for pdf_file in files:
                # Guardar el archivo PDF en el modelo
                pdf_instance = ProcessedPDF.objects.create(filename=pdf_file.name, file=pdf_file)
                text = extract_text_from_pdf(pdf_file)
                products = parse_products(text)
                for item in products:
                    if not Product.objects.filter(name=item.get('name'), model=item.get('model')).exists():
                        Product.objects.create(**item)
                        total_nuevos += 1
            if total_nuevos == 0:
                form.add_error(None, 'No se agregaron productos nuevos (posibles duplicados o PDFs vacíos).')
            else:
                return redirect('pdf_processor:product_list')
    else:
        form = MultiPDFUploadForm()

    # Mostrar los PDFs procesados recientemente
    pdfs = ProcessedPDF.objects.all().order_by('-uploaded_at')[:20]
    return render(request, 'processor.html', {'form': form, 'pdfs': pdfs})


def product_list_view(request):
    """Muestra la lista de productos cargados, ordenados por fecha de carga, con filtros manuales."""
    # Obtener valores únicos para los filtros
    brands = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
    categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')
    stores = Product.objects.values_list('store', flat=True).distinct().order_by('store')

    # Obtener valores seleccionados de los filtros
    selected_brand = request.GET.get('brand', '')
    selected_category = request.GET.get('category', '')
    selected_store = request.GET.get('store', '')

    products = Product.objects.all()
    if selected_brand:
        products = products.filter(brand=selected_brand)
    if selected_category:
        products = products.filter(category=selected_category)
    if selected_store:
        products = products.filter(store=selected_store)
    products = products.order_by('-uploaded_at')

    context = {
        'products': products,
        'brands': brands,
        'categories': categories,
        'stores': stores,
        'selected_brand': selected_brand,
        'selected_category': selected_category,
        'selected_store': selected_store,
    }
    return render(request, 'list_product.html', context)

def weekly_price_report(request):
    """Genera un reporte semanal de precios promedio por producto."""
    weekly_data = (
        Product.objects
        .annotate(week=TruncWeek('uploaded_at'))
        .values('name', 'week')
        .annotate(avg_price=Avg('price'))
        .order_by('name', 'week')
    )
    return render(request, 'processor/weekly_report.html', {'weekly_data': weekly_data})