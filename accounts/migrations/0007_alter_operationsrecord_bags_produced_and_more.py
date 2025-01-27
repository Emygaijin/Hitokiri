# Generated by Django 4.0.6 on 2024-12-23 10:26

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_salesrecord_alter_customuser_phone_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operationsrecord',
            name='bags_produced',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='operationsrecord',
            name='bags_pushed_to_sales',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='operationsrecord',
            name='bags_returned',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='operationsrecord',
            name='date_of_expense',
            field=models.DateField(blank=True, default=django.utils.timezone.now, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='operationsrecord',
            name='date_produced',
            field=models.DateField(blank=True, default=django.utils.timezone.now, editable=False, null=True),
        ),
    ]
