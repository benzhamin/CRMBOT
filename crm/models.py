from django.db import models

class Admins(models.Model):
    adminnumber = models.IntegerField()
    

class Product(models.Model):
    product_name = models.CharField(max_length=150)
    amount = models.IntegerField()

    def __str__(self):
        return self.product_name
    
class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=5)
    amount = models.IntegerField()
    comment = models.CharField(max_length=150)

    def __str__(self):
        return f"Order {self.id} - {self.product.product_name}"
# Create your models here.
