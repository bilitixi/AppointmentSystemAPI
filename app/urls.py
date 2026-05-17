from django.urls import path
from rest_framework.routers import DefaultRouter
from app.views import home

router = DefaultRouter()
urlpatterns =[
    path('', home, name='home')
]