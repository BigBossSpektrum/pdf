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

    # Lista de marcas conocidas
    known_brands = [
        "Samsung", "LG", "Sony", "Lenovo", "Asus",
        "HP", "Dell", "Acer", "Apple", "Xiaomi",
        "Motorola", "Huawei", "Canon", "Epson", "Brother"
    ]

    # Lista de palabras/frases a ignorar
    blacklist_keywords = {
        'x', '$', 'promo', 'oferta',
        'iva', 'iva incluido', 'original',
        'nuevo', 'nuevo original'
    }

    i = 0
    while i < len(lines):
        name = lines[i]
        price = None
        brand = ""
        category = ""
        model = ""
        description = ""

        # Filtro de líneas basura
        if name.lower() in blacklist_keywords or re.fullmatch(r"\d+", name):
            i += 1
            continue

        # Buscar precio
        for j in range(1, 4):
            if i + j < len(lines):
                line = lines[i + j]
                if price_match := re.search(
                    r"(\d+(?:[\.,]\d{1,2})?)\s*\$?", line
                ):
                    try:
                        price = float(price_match.group(1).replace(',', '.'))
                        i += j + 1
                        break
                    except ValueError:
                        continue

        # Extraer campos adicionales (modelo, descripción, etc.)
        metadata_limit = 3
        for k in range(1, metadata_limit + 1):
            if i + k < len(lines):
                meta_line = lines[i + k].lower()

                if 'marca:' in meta_line:
                    brand = meta_line.split('marca:')[-1].strip()
                elif 'categoría:' in meta_line or 'categoria:' in meta_line:
                    category = meta_line.split(':')[-1].strip()
                elif 'modelo:' in meta_line:
                    model = meta_line.split('modelo:')[-1].strip()
                elif 'desc:' in meta_line or 'descripcion:' in meta_line:
                    description = meta_line.split(':')[-1].strip()

        # **Filtrar descripciones**:
        # Ignorar si la descripción es solo números o tiene menos de 5 caracteres
        if description and (len(description) < 5 or description.isdigit()):
            description = ""  # Ignoramos descripciones incorrectas

        # Detección automática de marca si está vacía
        full_text = f"{name} {description}".lower()
        if not brand:
            for b in known_brands:
                if b.lower() in full_text:
                    brand = b
                    break

        if price and description:  # Solo guardamos el producto si tiene precio y una descripción válida
            products.append({
                'name': name,
                'price': price,
                'brand': brand or 'Desconocida',
                'category': category or 'General',
                'model': model,
                'description': description or name,
                'store': 'Manual',
            })

        i += 1

    print(f"📦 Productos parseados: {len(products)}")
    return products

