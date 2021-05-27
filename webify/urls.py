"""webify URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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

urlpatterns = [
    path('', include('main_page.urls')),
    path('main_page/', include('main_page.urls')),
    path('admin/', admin.site.urls),
    path('utilities/', include('plab_utilities.urls')),
    path('test_report_automation/', include('test_report_automation.urls')),
    path('db_refresher/', include('db_refresher.urls')),
    path('nl_project_manager/', include('nl_project_manager.urls')),
    path('nl_test_starter/', include('nl_test_starter.urls')),
    path('sla_sheet_generator/', include('sla_sheet_generator.urls')),
]
