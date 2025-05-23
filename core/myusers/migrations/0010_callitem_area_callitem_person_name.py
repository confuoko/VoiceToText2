# Generated by Django 4.2.20 on 2025-05-14 20:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("myusers", "0009_callitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="callitem",
            name="area",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="itemcalls",
                to="myusers.area",
                verbose_name="Область исследования",
            ),
        ),
        migrations.AddField(
            model_name="callitem",
            name="person_name",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="ФИО представителя"
            ),
        ),
    ]
