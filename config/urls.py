from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from finances.views import AppLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", AppLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("finances.urls")),
]
