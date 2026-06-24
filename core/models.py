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


class SystemSettings(models.Model):
    company = models.OneToOneField(Company,on_delete=models.CASCADE,related_name="settings")
    currency = models.CharField(max_length=10,default="INR")
    financial_year_start = models.DateField()
    financial_year_end = models.DateField()
    allow_negative_balance = models.BooleanField(default=False)
    default_commission = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
    def __str__(self):
        return f"{self.company.company_name} Settings"