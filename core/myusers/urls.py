from django.urls import path
from .views import WelcomeView, AudioDownloadView, TextDownloadView, SuccessDownloadView, CallListView, \
    NewCallListView, CallItemEditView, CallItemDeleteView

app_name = "myusers"  # Добавляем пространство имен

urlpatterns = [
    path("welcome/", WelcomeView.as_view(), name="welcome"),  # Главная страница
    path("audio/download/", AudioDownloadView.as_view(), name="audio_download"),
    path("text/download/", TextDownloadView.as_view(), name="text_download"),
    path("success/download/", SuccessDownloadView.as_view(), name="success_download"),


    path("call/list", CallListView.as_view(), name="call_list"),  # Персональный список касаний
    path("new_call/", NewCallListView.as_view(), name="new_call_list"),  # Полный список касаний
    path('call_item/edit/<int:pk>/', CallItemEditView.as_view(), name='edit_call_item'),
    path('call_item/delete/<int:pk>/', CallItemDeleteView.as_view(), name='delete_call_item'),
]
