# Generated by Django 3.1.5 on 2021-02-05 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_auto_20210131_1023'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='booking_id',
            field=models.CharField(default=None, editable=False, max_length=32),
            preserve_default=False,
        ),
    ]