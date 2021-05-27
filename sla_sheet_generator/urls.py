from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='sla-sheet-generator-home'),
    # path('about/', views.about, name='plab-util-about'),
    # path('test/', views.test, name='plab-util-about'),
]
