from django.contrib import admin
from .models import Admins, Order, Product

admin.site.register(Admins)
admin.site.register(Order)
admin.site.register(Product)

# Register your models here.
