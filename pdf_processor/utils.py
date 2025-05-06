import pymupdf as fitz  # PyMuPDF
import re
from .forms import UploadPDFForm
from django.shortcuts import render, redirect
from .models import Product
from io import BytesIO

def extract_text_from_pdf(pdf_file):
    try:
        # Leer el contenido del archivo
        raw_data = pdf_file.read()
        if not raw_data:
            print("⚠️ El archivo PDF está vacío.")
            return ""

        file_bytes = BytesIO(raw_data)

        # Abrir el PDF con fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        if doc.page_count == 0:
            print("⚠️ El PDF no contiene páginas.")
            return ""

        # Extraer texto
        text = "".join(page.get_text() for page in doc)

        if not text.strip():
            print("⚠️ No se extrajo texto del PDF.")
            return ""

        print("✅ Texto extraído del PDF correctamente.")
        print("📄 Primeros 500 caracteres del texto extraído:\n", text[:500])
        return text

    except Exception as e:
        print("❌ Error al leer el PDF:", e)
        return ""

def upload_pdf_view(request):
    if request.method == 'POST':
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data['pdf_file']

            # EXTRAER TEXTO DEL PDF
            try:
                text = extract_text_from_pdf(pdf_file)
                print("\n=== TEXTO EXTRAÍDO DEL PDF ===\n", text)
            except Exception as e:
                print("❌ Error al extraer texto del PDF:", e)
                return render(request, 'upload_pdf.html', {
                    'form': form,
                    'error': 'No se pudo extraer texto del PDF.'
                })

            # PARSEAR LOS PRODUCTOS
            try:
                products = parse_products(text)
                print("\n=== PRODUCTOS PARSEADOS ===\n", products)
            except Exception as e:
                print("❌ Error al parsear productos:", e)
                return render(request, 'upload_pdf.html', {
                    'form': form,
                    'error': 'No se pudo analizar el contenido del PDF.'
                })

            # GUARDAR EN LA BASE DE DATOS
            for item in products:
                try:
                    print("💾 Guardando producto:", item)
                    Product.objects.create(**item)
                except Exception as e:
                    print("❌ Error al guardar producto:", e)
                    continue  # Podés omitir este producto pero seguir con los demás

            return redirect('pdf_processor:product_list')

    else:
        form = UploadPDFForm()

    return render(request, 'upload_pdf.html', {'form': form})


def parse_products(text):
    import re

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    products = []

    i = 0
    while i < len(lines):
        name_candidate = lines[i]
        price = None

        # Filtrar líneas basura
        if name_candidate.lower() in {'x', '$'} or re.fullmatch(r"\d+", name_candidate):
            i += 1
            continue

        # Revisa las siguientes líneas por un posible precio
        for j in range(1, 3):
            if i + j < len(lines):
                candidate = lines[i + j]
                match = re.search(r"(\d+(?:[\.,]\d{1,2})?)\s*\$?", candidate)
                if match:
                    try:
                        price = float(match.group(1).replace(',', '.'))
                        i += j + 1
                        break
                    except ValueError:
                        continue

        if price:
            products.append({
                'name': name_candidate,
                'price': price,
                'description': name_candidate,  # Se usa como descripción por ahora
                'store': 'Manual',
                'model': ''
            })
        else:
            i += 1

    print(f"📦 Productos parseados: {len(products)}")
    return products