import datetime
import time
import os
import logging
import re

import boto3
import requests
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, ListView
from dotenv import load_dotenv

from myusers.models import User, AudioTextFile, Area, Call, TextPure, Company, Opponent, Purpose, CallItem



from django.views.generic.edit import View, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.forms import modelform_factory



# Настраиваем логгер
logger = logging.getLogger(__name__)

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User  # Используем нашу кастомную модель
        fields = ("username", "first_name", "last_name", "email", "position", "password1", "password2")

# Вьюха для регистрации
class SignUpView(CreateView):
    form_class = CustomUserCreationForm  # Используем кастомную форму
    template_name = "registration/signup.html"
    success_url = reverse_lazy("myusers:welcome")  # Перенаправляем на главную после регистрации

# Главная страница с приветствием
class WelcomeView(LoginRequiredMixin, TemplateView):
    template_name = "welcome.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["username"] = self.request.user.username  # Передаем имя пользователя
        return context


# Страница загрузки аудиофайлов
class AudioDownloadView(LoginRequiredMixin, TemplateView):
    template_name = "audio_download.html"
    success_url = "myusers:success_download"

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("audio_file")
        start_time = time.time()  # Запоминаем время начала обработки

        if not uploaded_file or not uploaded_file.name.endswith((".wav", ".mp3", ".ogg")):
            return self.render_to_response({"error": "Файл должен быть в формате .wav, .mp3 или .ogg"})

        # Генерируем путь для сохранения
        file_name, file_ext = os.path.splitext(uploaded_file.name)
        current_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Формат даты и времени: YYYYMMDD_HHMMSS
        new_file_name = f"{file_name}_{current_timestamp}{file_ext}"

        # Параметры S3
        load_dotenv()
        AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
        AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket_name = "whisper-audiotest"

        # Инициализация клиента S3
        s3 = boto3.client(
            's3',
            endpoint_url="http://storage.yandexcloud.net",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        # Сохранение файла в S3
        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=new_file_name,  # Сохранение под новым именем
                Body=uploaded_file.read(),
                ContentType="audio/wav"
            )
            print(f"Файл сохранён в S3: {new_file_name}")
        except Exception as e:
            print(f"Ошибка при сохранении в S3: {e}")
            return self.render_to_response({"error": "Ошибка при сохранении файла в S3"})

        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Время обработки: {processing_time} секунд")

        # Получаем выбранную территорию
        area_id = request.POST.get("area")  # id выбранной области
        area_instance = Area.objects.filter(id=area_id).first()  # находим объект области по id

        # Получаем значение чекбокса
        preprocessing_required = request.POST.get('preprocessing_required') == 'on'  # Проверяем, был ли чекбокс установлен

        # Создаем экземпляр звонка
        call_instance = CallItem.objects.create(
            user=request.user,
            area=area_instance,  # Сохраняем выбранную территорию
            name_input=uploaded_file.name,
            name_save=new_file_name,
            data_save=datetime.date.today(),
            is_audio=True,
            lead=None,
            do_clean=preprocessing_required  # Сохраняем значение чекбокса
        )

        # Получение id
        call_id = call_instance.id
        print(f"Созданный звонок имеет ID: {call_id}")

        # Направляем запрос в сервис Обработчик аудио, передаем id и имя файла и флаг, нужно ли очищать аудио
        print('Параметры, переданные в сервис по предобработке:')
        print(call_id)
        print(new_file_name)
        print(preprocessing_required)

        RUNPOD_AUTH_TOKEN = os.getenv("RUNPOD_AUTH_TOKEN")
        FILTER_QUEUE = os.getenv("FILTER_QUEUE")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': RUNPOD_AUTH_TOKEN
        }

        data = {
            'input':
                {
                    "file_key": new_file_name,
                    "do_clean": preprocessing_required,
                    "item_id": call_id
                }
        }

        response = requests.post(f'https://api.runpod.ai/v2/{FILTER_QUEUE}/run', headers=headers, json=data)

        print(f"HTTP статус код: {response.status_code}")
        if response.status_code == 200:
            print(f"Отправляем запрос к сервису Предобработки. Ответ: {response.json()}")
        else:
            print(f"Ошибка при отправке запроса: {response.text}")

        return redirect(self.success_url)  # Перенаправляем на страницу успешной загрузки

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["error"] = self.request.GET.get("error", None)  # Передаем ошибки в шаблон
        context["areas"] = Area.objects.all()  # Передаем все области для выбора
        return context




# Страница загрузки текстовых файлов
class TextDownloadView(LoginRequiredMixin, TemplateView):
    template_name = "text_download.html"
    success_url = "myusers:success_download"

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("text_file")
        start_time = time.time()  # Запоминаем время начала обработки

        # Получаем выбранную территорию из формы
        area_id = request.POST.get("area")  # id выбранной области
        area_instance = Area.objects.filter(id=area_id).first()  # находим объект области по id

        if not uploaded_file or not uploaded_file.name.endswith(".txt"):
            return self.render_to_response({"error": "Файл должен быть в формате .txt"})

        # Генерируем путь для сохранения
        file_name, file_ext = os.path.splitext(uploaded_file.name)
        current_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Формат даты и времени: YYYYMMDD_HHMMSS
        new_file_name = f"{file_name}_{current_timestamp}{file_ext}"

        # Параметры S3
        load_dotenv()
        AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
        AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket_name = "whisper-audiotest"

        # Инициализация клиента S3
        s3 = boto3.client(
            's3',
            endpoint_url="http://storage.yandexcloud.net",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        # Сохранение файла в S3
        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=new_file_name, # Сохранение под новым именем
                Body=uploaded_file.read(),
                ContentType="text/plain"
            )
            print(f"Файл сохранён в S3: {new_file_name}")
        except Exception as e:
            print(f"Ошибка при сохранении в S3: {e}")
            return self.render_to_response({"error": "Ошибка при сохранении файла в S3"})

        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Время обработки: {processing_time} секунд")

        # Создаем экземпляр звонка
        call_instance = CallItem.objects.create(
            user=request.user,
            area=area_instance,  # Сохраняем выбранную территорию
            name_input=uploaded_file.name,
            name_save=new_file_name,
            data_save=datetime.date.today(),
            is_audio=False,
            lead=None,
        )

        # Получение id
        call_id = call_instance.id
        print(f"Созданный звонок имеет ID: {call_id}")

        # Направляем запрос в сервис кластеризации
        print("Передаем параметры в сервис Кластеризации:")
        print(call_id)
        print(new_file_name)

        RUNPOD_AUTH_TOKEN = os.getenv("RUNPOD_AUTH_TOKEN")
        CLASTER_QUEUE = os.getenv("CLASTER_QUEUE")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': RUNPOD_AUTH_TOKEN
        }

        data = {
            'input':
                {
                    "file_key": new_file_name,
                    "item_id": call_id
                }
        }
        print(f"Направляю файл: {new_file_name} и ID записи: {call_id}")

        response = requests.post(f'https://api.runpod.ai/v2/{CLASTER_QUEUE}/run', headers=headers, json=data)
        print(f"HTTP статус код: {response.status_code}")
        if response.status_code == 200:
            print(f"Отправляем запрос к сервису Предобработки. Ответ: {response.json()}")
        else:
            print(f"Ошибка при отправке запроса: {response.text}")

        return redirect(self.success_url)  # Перенаправляем на страницу успешной загрузки

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["error"] = self.request.GET.get("error", None)  # Передаем ошибки в шаблон
        context["areas"] = Area.objects.all()  # Передаем все области для выбора
        return context

class SuccessDownloadView(LoginRequiredMixin, TemplateView):
    template_name = "success_download.html"


class CallListView(LoginRequiredMixin, TemplateView):
    model = CallItem
    template_name = 'myusers/call_list.html'
    context_object_name = 'call_items'
    paginate_by = 5  # Настроим пагинацию, чтобы показывать по 5 объектов на странице

    # Укажем, какие поля будем отображать в шаблоне
    fields_to_display = [
        'user', 'company_name', 'telephone', 'person_name', 'position', 'responsibility',
        'name_input', 'name_save', 'name_audio_to_txt', 'name_file_cleaned', 'data_save',
        'is_audio', 'do_clean', 'audio_length', 'description', 'data_type', 'data_type_short',
        'amount', 'price_month', 'price_one_file', 'lead', 'fail_reason', 'area_name', 'area', 'next_place'
    ]

    def get_queryset(self):
        """
        Здесь можно настроить фильтрацию или сортировку.
        В данный момент просто возвращаем все объекты.
        """
        return CallItem.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields_to_display'] = self.fields_to_display  # Передаем список полей для отображения
        return context


class NewCallListView(ListView):
    model = CallItem
    template_name = 'new_call_list.html'
    context_object_name = 'call_items'
    paginate_by = 5  # Настроим пагинацию, чтобы показывать по 5 объектов на странице

    fields_to_display = [
        'user', 'company_name', 'telephone', 'person_name', 'position', 'responsibility',
        'name_input', 'name_save', 'name_audio_to_txt', 'name_file_cleaned', 'data_save',
        'is_audio', 'do_clean', 'audio_length', 'description', 'data_type', 'data_type_short',
        'amount', 'price_month', 'price_one_file', 'lead', 'fail_reason', 'area_name', 'area', 'next_place'
    ]

    def get_queryset(self):
        queryset = CallItem.objects.all()

        # Фильтрация по пользователю
        user_filter = self.request.GET.get('user')
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)

        # Фильтрация по дате загрузки
        date_filter = self.request.GET.get('data_save')
        if date_filter:
            queryset = queryset.filter(data_save=date_filter)

        # Фильтрация по успешности касания
        lead_filter = self.request.GET.get('lead')
        if lead_filter:
            queryset = queryset.filter(lead=lead_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавление отладки
        print("Paginator:", context['paginator'])
        print("Page Object:", context['page_obj'])

        context['total_pages'] = context['paginator'].num_pages  # Всего страниц
        context['current_page'] = context['page_obj'].number  # Текущая страница

        context['fields_to_display'] = self.fields_to_display  # Передаем список полей для отображения
        context['call_items_count'] = self.get_queryset().count()  # Количество записей
        return context


class CallItemEditView(UpdateView):
    model = CallItem
    fields = ['company_name', 'telephone', 'person_name', 'position', 'responsibility',
              'name_input', 'data_save', 'description', 'data_type',
              'amount', 'price_month', 'price_one_file', 'lead', 'fail_reason', 'area', 'next_place']
    template_name = 'call_item_edit.html'
    context_object_name = 'call_item'

    def get_success_url(self):
        return reverse_lazy('myusers:new_call_list')  # После редактирования перенаправляем на список


class CallItemDeleteView(DeleteView):
    model = CallItem
    template_name = 'call_item_confirm_delete.html'
    context_object_name = 'call_item'
    success_url = reverse_lazy('myusers:new_call_list')  # Перенаправление на список после удаления

