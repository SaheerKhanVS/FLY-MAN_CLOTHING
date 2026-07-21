from django.db import models


class Company(models.Model):
    company_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    logo = models.ImageField(upload_to="company/logos/",blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
    def __str__(self):
        return self.company_name
    

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"

class Color(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hex_code = models.CharField(max_length=7)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

class SystemSettings(models.Model):
    company = models.OneToOneField(Company,on_delete=models.CASCADE,related_name="settings")
    currency = models.ForeignKey(Currency,on_delete=models.PROTECT)
    financial_year_start = models.DateField()
    financial_year_end = models.DateField()
    allow_negative_balance = models.BooleanField(default=False)
    default_commission = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
    primary_color = models.ForeignKey(Color,on_delete=models.SET_NULL, null=True,blank=True,related_name="primary_settings")
    secondary_color = models.ForeignKey(Color, on_delete=models.SET_NULL,null=True, blank=True, related_name="secondary_settings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
    def __str__(self):
        return f"{self.company.company_name} Settings"
    
