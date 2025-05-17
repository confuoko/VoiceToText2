from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class User(AbstractUser):
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Должность")
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)


# Компания
class Company(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название компании")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    worker = models.ForeignKey("Opponent", on_delete=models.SET_NULL, null=True, blank=True, related_name="companies",
                               verbose_name="Должностное лицо")

    def __str__(self):
        return self.title


# Должностное лицо (оппонент)
class Opponent(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Имя (генерируемое)")
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Должность")
    responsibility = models.TextField(blank=True, null=True, verbose_name="Область ответственности")

    def save(self, *args, **kwargs):
        if not self.name:
            last_id = Opponent.objects.all().count() + 1
            self.name = f"worker_{last_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Файл, загружаемый пользователем
class AudioTextFile(models.Model):
    name_input = models.CharField(max_length=255, verbose_name="Исходное название файла")
    name_save = models.CharField(max_length=255, verbose_name="Сохраненное название файла")
    data_save = models.DateField(verbose_name="Дата сохранения")
    #saver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_files",
                              # verbose_name="Загрузивший пользователь", null=True, blank=True)
    is_audio = models.BooleanField(default=False, verbose_name="Является аудиофайлом")

    def __str__(self):
        return self.name_save


# Текст, выделенный из файла
class TextPure(models.Model):
    id_doc = models.OneToOneField(AudioTextFile, on_delete=models.CASCADE, related_name="text_content",
                                  verbose_name="Файл", null=True, blank=True)
    text = models.TextField(verbose_name="Текст из файла")

    def __str__(self):
        return f"Текст из {self.id_doc.name_save}"


# Область исследования
class Area(models.Model):
    area_name = models.CharField(max_length=255, verbose_name="Название области")

    def __str__(self):
        return self.area_name


# Цель переговоров
class Purpose(models.Model):
    description = models.TextField(blank=True, null=True, verbose_name="Описание запроса")
    data_type = models.CharField(max_length=255, blank=True, null=True, verbose_name="Тип данных")
    data_type_short = models.CharField(max_length=255, blank=True, null=True, verbose_name="Краткий тип данных")
    amount = models.IntegerField(blank=True, null=True, verbose_name="Желаемый объем данных в месяц")
    price_month = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Цена за месяц")
    price_one_file = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Цена за один файл")

    def __str__(self):
        return f"Цель: {self.description[:50]}" if self.description else "Цель переговоров"


# Звонок
class Call(models.Model):
    LEAD_CHOICES = [
        ("success", "Успех"),
        ("fail", "Неудача"),
        ("hesitant", "Неопределённый"),
        (None, "Нет данных"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="calls", verbose_name="Пользователь")
    opponent = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name="calls", verbose_name="Компания")
    text_file = models.OneToOneField(AudioTextFile, on_delete=models.CASCADE, null=True, blank=True, related_name="call", verbose_name="Файл")
    purpose = models.ForeignKey(Purpose, on_delete=models.SET_NULL, null=True, blank=True, related_name="calls",
                                verbose_name="Цель переговоров")
    lead = models.CharField(max_length=10, choices=LEAD_CHOICES, null=True, blank=True, verbose_name="Итог звонка")
    fail_reason = models.TextField(blank=True, null=True, verbose_name="Причина отказа")
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name="calls",
                             verbose_name="Область исследования")

    def __str__(self):
        return f"Звонок {self.user.username} с {self.opponent.title}"


class CallItem(models.Model):
    LEAD_CHOICES = [
        ("success", "Успех"),
        ("fail", "Неудача"),
        ("hesitant", "Неопределённый"),
        (None, "Нет данных"),
    ]

    # Основные поля
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="call_items", verbose_name="Пользователь")
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Название компании")
    telephone = models.CharField(max_length=255, blank=True, null=True, verbose_name="Телефон представителя")
    person_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="ФИО представителя")
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Должность представителя")
    responsibility = models.TextField(blank=True, null=True, verbose_name="Зона ответственности")

    # Информация о файле
    name_input = models.CharField(max_length=255, verbose_name="Исходное название файла")
    name_save = models.CharField(max_length=255, unique=True, verbose_name="Сохраненное название файла")
    name_audio_to_txt = models.CharField(max_length=255, blank=True, null=True, verbose_name="Название транскрибированного текстового файла")
    name_file_cleaned = models.CharField(max_length=255, blank=True, null=True,
                                         verbose_name="Название очищенного аудио файла")
    data_save = models.DateField(verbose_name="Дата загрузки", blank=True, null=True)
    is_audio = models.BooleanField(default=False, verbose_name="Аудиофайл")
    do_clean = models.BooleanField(default=False, verbose_name="Необходимость в предобработке")
    audio_length = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                       verbose_name="Длина аудиозаписи")

    # Информация о запросе
    description = models.TextField(blank=True, null=True, verbose_name="Описание запроса")
    data_type = models.CharField(max_length=255, blank=True, null=True, verbose_name="Тип данных")
    data_type_short = models.CharField(max_length=255, blank=True, null=True, verbose_name="Краткий тип данных")
    amount = models.IntegerField(blank=True, null=True, verbose_name="Количество документов в месяц")
    price_month = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                      verbose_name="Цена за месяц")
    price_one_file = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                         verbose_name="Цена за файл")

    # Итоги взаимодействия
    lead = models.CharField(max_length=10, choices=LEAD_CHOICES, null=True, blank=True,
                            verbose_name="Успешность касания")
    fail_reason = models.TextField(blank=True, null=True, verbose_name="Причина отказа")

    # Область исследования
    area_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Наименование области")
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name="itemcalls",
                             verbose_name="Область исследования")
    next_place = models.CharField(max_length=255, blank=True, null=True, verbose_name="Время и место следующей встречи")


    class Meta:
        verbose_name = "Касание"
        verbose_name_plural = "Касания"
        unique_together = ("id", "name_save")

    def __str__(self):
        return f"{self.name_input} - {self.company_name or 'Без компании'}"