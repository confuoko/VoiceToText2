# Generated by Django 4.2.20 on 2025-05-15 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myusers", "0012_callitem_telephone"),
    ]

    operations = [
        migrations.AddField(
            model_name="callitem",
            name="name_audio_to_txt",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Название транскрибированного текстового файла",
            ),
        ),
    ]
