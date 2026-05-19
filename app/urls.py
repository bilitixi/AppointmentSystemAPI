from django.urls import path
from rest_framework.routers import DefaultRouter
from app.views import home
from app.viewsets import DoctorViewSet, AppointmentSlotViewSet, AppointmentViewSet, PatientViewSet

router = DefaultRouter()

router.register('doctors', DoctorViewSet)
router.register('appointment_slots', AppointmentSlotViewSet)
router.register('appointments', AppointmentViewSet)
router.register('patients', PatientViewSet)

urlpatterns =[
    path('', home, name='home')
] + router.urls