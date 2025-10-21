from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'gallery'

urlpatterns = [
    path("", views.single_page_view, name="index"),
    path("api/gallery/", views.gallery_api, name="gallery_api"),
    path("api/gallery/tags/", views.gallery_tags_api, name="gallery_tags_api"),
    path("contact/", views.contact_form_view, name="contact_form"),
    path('gallery/',views.single_page_view, name='gallery'),
]