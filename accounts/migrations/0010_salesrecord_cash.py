# Generated by Django 4.0.6 on 2025-01-13 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_salesrecord_bags_received_from_production_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesrecord',
            name='cash',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
