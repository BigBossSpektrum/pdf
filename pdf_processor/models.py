from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, default='Desconocida')
    category = models.CharField(max_length=255, default='Desconocida')
    description = models.TextField()
    store = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
