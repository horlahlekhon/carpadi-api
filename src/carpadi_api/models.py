from django.db import models

# Create your models here.

class Transction(models.Model):
    id = models.UUIDField
    wallet = models.UUIDField
    amount = models.DecimalField
