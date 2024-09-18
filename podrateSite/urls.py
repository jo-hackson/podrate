from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("podrate/", include("podrate.urls")),
    path("admin/", admin.site.urls),
]