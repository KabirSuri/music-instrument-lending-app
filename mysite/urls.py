"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib import messages
from django.shortcuts import redirect
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include("allauth.urls")),
    path('', views.catalog_view, name='catalog'),
    path('patron-landing/', views.patron_login, name='patron-landing'),
    path('librarian-landing/', views.librarian_login, name='librarian-landing'),
    path('profile/', views.profile_view, name='profile'),
    path('image_upload/', views.image_upload_view, name='image_upload'),
    path('borrow/<int:item_id>/', views.borrow_item, name="borrow_item"),
    path('items/', views.search_items, name="search_items"),
    path('items/<int:item_id>/', views.item_detail, name="item_detail"),
    path('create-item/', views.create_item, name='create-item'),
    path('edit-item/<int:item_id>/', views.edit_item, name='edit-item'),
    path('delete-item/<int:item_id>/', views.delete_item, name='delete_item'),
    path('items/<int:item_id>/rate/', views.rate_item, name='rate_item'),
    # Collection URLs
    path('collections/', views.collection_list, name='collections'),
    path('collections/create/', views.create_collection, name='create-collection'),
    path('collections/<int:collection_id>/', views.collection_detail, name='collection-detail'),
    path('collections/<int:collection_id>/edit/', views.edit_collection, name='edit-collection'),
    path('collections/<int:collection_id>/delete/', views.delete_collection, name='delete-collection'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
