from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="get_podcast"),
    path("about/", views.AboutMeView.as_view(), name="about-me")
]

