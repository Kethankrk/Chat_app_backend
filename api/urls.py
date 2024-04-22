from django.urls import path
from .views import loginView, userRegisterView, searchUserView, friendRequestView, chatView, inboxView

urlpatterns = [
    path("login/", loginView),
    path("signup/", userRegisterView),
    path("find/", searchUserView),
    path("request/", friendRequestView.as_view()),
    path("chat/", chatView.as_view()),
    path("inbox/", inboxView.as_view()),
]
