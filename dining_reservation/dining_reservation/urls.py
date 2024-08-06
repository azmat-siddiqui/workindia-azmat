"""
URL configuration for dining_reservation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from zomato import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include('zomato.urls')),
    path('api/signup/', views.signup, name='signup'),
    path('api/login/', views.user_login, name='login'),
    path('api/dining-place/create/', views.create_dining_place, name='create_dining_place'),
    path('api/dining-place/', views.search_dining_places, name='search_dining_places'),
    path('api/dining-place/<int:place_id>/availability/', views.check_availability, name='check_availability'),
    path('api/dining-place/book/', views.book_dining_place, name='book_dining_place'),
    path('api/dining-place/<int:place_id>/delete/', views.delete_dining_place, name='delete_dining_place'),
]