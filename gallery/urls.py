from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'gallery'

urlpatterns = [
    path("", views.index_view, name="index"),
    path("gallery/", views.gallery_view, name="gallery"),
    path("api/gallery/", views.gallery_api, name="gallery_api"),
    path("api/gallery/tags/", views.gallery_tags_api, name="gallery_tags_api"),
    path("contact/", views.contact_form_view, name="contact_form"),
]