from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.timezone import now


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Finance', 'finance'),
        ('Operations Manager', 'Operations Manager'),
        ('Sales', 'sales'),
        ('Driver', 'driver'),
        ('Bagger', 'bagger'),
        ('Cleaner', 'cleaner'),
        ('Motor boy', 'motor boy'),
        ('Security', 'security'),
        ('Supervisor', 'supervisor')
        # Add remaining roles...
    ]
    STATUS_CHOICES = [
        ('Engaged', 'Engaged'),
        ('Disengaged', 'Disengaged'),
    ]

    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateField(default=now)  # Fixed to have a default value
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Engaged')
    date_disengaged = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.name} {self.surname} - {self.role}"


class OperationsRecord(models.Model):
    bags_produced = models.PositiveIntegerField(blank=True, null=True)
    date_produced = models.DateField(default=now, editable=False, blank=True, null=True)
    bags_returned = models.PositiveIntegerField(default=0, blank=True, null=True)
    bags_pushed_to_sales = models.PositiveIntegerField(default=0, blank=True,null=True)
    stereo_received = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    stereo_used = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    packaging_bags = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    packaging_bags_used = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    bad_stereo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    comments = models.TextField(blank=True, max_length=2035)


    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(bags_pushed_to_sales__lte=models.F('bags_produced')),
                name='bags_pushed_to_sales_lte_bags_produced'
            ),
        ]

    def __str__(self):
        return f"Record for {self.date_produced} - Bags Produced: {self.bags_produced}"


class SalesRecord(models.Model):
    bags_received_from_production = models.PositiveIntegerField(default=0)
    applied_discount = models.PositiveIntegerField(default=0)
    bags_sold = models.PositiveIntegerField()
    bags_returned = models.PositiveIntegerField(default=0)
    date_of_sale = models.DateField(default=now, editable=False)
    keystone = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    zenith = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    moniepoint = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comments = models.TextField(blank=True, max_length=2035)

    def calc(self):
        # Ensure none of the fields are None before calculating
        return (self.keystone or 0) + (self.moniepoint or 0) + (self.zenith or 0) + self.cash

    def save(self, *args, **kwargs):
        # Automatically calculate the total before saving
        self.total = self.calc()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sales on {self.date_of_sale}: Sold - {self.bags_sold}, Returned - {self.bags_returned}"


class Finance(models.Model):
    expense_title = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_of_expense = models.DateField(default=now, editable=False, blank=True, null=True)
    receipt = models.FileField(upload_to='expenses_receipts/', blank=True, null=True)
    comments = models.TextField(blank=True, max_length=2035)

