# Generated by Django 3.1.5 on 2021-02-07 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_auto_20210131_2216'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactusmessage',
            name='reference',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
