from django.urls import path
from .views import WelcomeView, AudioDownloadView, TextDownloadView, SuccessDownloadView, CallListView

app_name = "myusers"  # Добавляем пространство имен

urlpatterns = [
    path("welcome/", WelcomeView.as_view(), name="welcome"),  # Главная страница
    path("audio/download/", AudioDownloadView.as_view(), name="audio_download"),
    path("text/download/", TextDownloadView.as_view(), name="text_download"),
    path("success/download/", SuccessDownloadView.as_view(), name="success_download"),

    path("call/list", CallListView.as_view(), name="call_list"),  # Персональный список касаний
]
