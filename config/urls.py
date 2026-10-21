
from django.contrib import admin
from django.urls import path
from chatbot.views import sunny_chat

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat/", sunny_chat, name="sunny-chat"),
]
