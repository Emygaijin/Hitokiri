# Generated by Django 4.0.6 on 2025-01-24 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_alter_customuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesrecord',
            name='cash',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
