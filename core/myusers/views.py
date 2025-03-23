import datetime
import os

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from myusers.models import User, AudioTextFile, Area, Call, TextPure, Company, Opponent

from .claster_model.claster_func import get_clusters


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
        # Не сохраняем файл, а сразу редиректим на успешную страницу
        return redirect('myusers:success_download')



# Страница загрузки текстовых файлов
class TextDownloadView(LoginRequiredMixin, TemplateView):
    template_name = "text_download.html"
    success_url = "myusers:success_download"  # Используем в redirect()

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("text_file")

        if not uploaded_file or not uploaded_file.name.endswith(".txt"):
            return self.render_to_response({"error": "Файл должен быть в формате .txt"})

        # Генерируем путь для сохранения
        save_path = os.path.join("uploads", uploaded_file.name)
        saved_file_path = default_storage.save(save_path, ContentFile(uploaded_file.read()))

        # Создаем экземпляр AudioTextFile
        text_file_instance = AudioTextFile.objects.create(
            name_input=uploaded_file.name,
            name_save=saved_file_path,
            data_save=datetime.date.today(),
            is_audio=False
        )

        # Считываем текст из файла
        uploaded_file.seek(0)  # Перемещаем указатель в начало файла
        text = uploaded_file.read().decode("utf-8")  # Считываем файл как текст

        # Создаем экземпляр TextPure и сохраняем туда текст
        text_pure_instance = TextPure.objects.create(
            id_doc=text_file_instance,  # Ссылаемся на только что созданный объект AudioTextFile
            text=text  # Сохраняем текст из файла
        )


        # Получаем объект Area с id=2
        area_instance = Area.objects.filter(id=2).first()

        # Создаем экземпляр Call
        call_instance = Call.objects.create(
            user=request.user,
            text_file=text_file_instance,
            area=area_instance
        )

        # Получаем результат из модели
        result = get_clusters(text)
        print(result)
        # Инициализация переменных - в переменных лежит список строк, брать всегда первое значение
        doc_value = result.get('DOC', None)  # тип документа, Purpose.data_type, модель ожидает строку
        mdt_value = result.get('MDT', None)  # время следующей встречи, модель ожидает строку
        name_value = result.get('NAME', None)  # имя представителя компании, Opponent.name модель ожидает строку
        o_value = result.get('O', None)  # хз, спросить
        org_value = result.get('ORG', None)  # название компании, склеивем все строки в одну строку
        pos_value = result.get('POS', None)  # хз, спросить
        tel_value = result.get('TEL', None)  # телефон, берем первое значение из списка
        vol_value = result.get('VOL', None)  # объем данных, Purpose.amount модель ожидает число

        # Вывод значений переменных для проверки
        print("DOC:", doc_value)
        print("MDT:", mdt_value)
        print("NAME:", name_value)
        print("O:", o_value)
        print("ORG:", org_value)
        print("POS:", pos_value)
        print("TEL:", tel_value)
        print("VOL:", vol_value)

        # Получаем название компании
        org_value = result.get('ORG', None)
        if org_value:
            company_name = ' '.join(org_value)  # Склеиваем все строки в одну строку
        else:
            # Генерируем уникальное название
            count = Company.objects.count() + 1
            company_name = f"Компания №{count}"

        # Получаем телефон компании
        tel_value = result.get('TEL', None)
        if tel_value:
            company_phone = tel_value[0]  # Берем первый телефон из списка
        else:
            company_phone = None

        # Создаем экземпляр Company
        company_instance = Company.objects.create(
            title=company_name,
            telephone=company_phone,
            worker=None  # Сначала присваиваем None, привязка будет ниже
        )

        # Привязываем компанию к модели Call
        call_instance.opponent = company_instance  # Привязываем компанию к полю "opponent"
        call_instance.save()

        # Склеиваем строки в имя представителя, если ключ 'NAME' присутствует
        name_value = result.get('NAME', None)
        if name_value:
            representative_name = ' '.join(name_value)  # Склеиваем строки
        else:
            representative_name = None

        # Проверяем, существует ли уже оппонент с таким именем
        if representative_name:
            counter = 1
            # Ищем, есть ли уже оппонент с таким именем
            while Opponent.objects.filter(name=representative_name).exists():
                # Если существует, увеличиваем счетчик и добавляем к имени
                representative_name = f"{representative_name} {counter}"
                counter += 1

        # Создаем экземпляр Opponent
        opponent_instance = Opponent.objects.create(
            name=representative_name,  # Присваиваем имя
            position=None,  # Позиция будет None, так как данных нет
            responsibility=None  # Ответственность будет None, так как данных нет
        )




        # Привязываем созданного оппонента к компании
        if company_instance:  # Убедитесь, что компания существует
            company_instance.worker = opponent_instance
            company_instance.save()  # Сохраняем изменения в компании






        return redirect(self.success_url)  # Перенаправляем на страницу успешной загрузки

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["error"] = self.request.GET.get("error", None)  # Передаем ошибки в шаблон
        return context

class SuccessDownloadView(LoginRequiredMixin, TemplateView):
    template_name = "success_download.html"

class CallListView(LoginRequiredMixin, TemplateView):
    template_name = "call_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["username"] = self.request.user.username  # Передаем имя пользователя
        context["calls"] = Call.objects.filter(user=self.request.user)  # Все звонки текущего пользователя
        return context