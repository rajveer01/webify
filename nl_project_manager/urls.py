from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='nl-project-manager-home'),
    path('print_me/', views.print_me, name='nl-project-manager-print-me'),
]
