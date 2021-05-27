from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='test-report-automation-home'),
    path('apps/', views.apps_name, name='test-report-automation-app-name'),
    path('base/', views.base, name='test-report-automation-base'),
    path('max_run/', views.max_run, name='test-report-automation-max-run'),
    path('max_run_old/', views.max_run_old, name='test-report-automation-max-run-old'),
]
