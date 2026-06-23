from django.db import models

class TestDocument(models.Model):
    title = models.CharField(max_length=100)

    pdf = models.FileField(
        upload_to='documents/'
    )
