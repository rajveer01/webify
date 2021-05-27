from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='plab-home'),
    path('app_parameters/', views.app_parameters, name='main-page-app-parameters'),
    path('app_parameters_submit/', views.app_parameters_submit, name='main-page-app-parameters-submit'),
    path('helper_db/', views.helper_db, name='helper-db-parameters'),
    path('run_tracker/', views.run_tracker, name='main-page-run-tracker'),
]
