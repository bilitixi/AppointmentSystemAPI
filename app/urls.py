from django.urls import path
from rest_framework.routers import DefaultRouter
from app.viewsets import DoctorViewSet, AppointmentSlotViewSet, AppointmentViewSet, PatientViewSet, UserViewSet, \
    RegisterViewSet, check_auth, me, doctors_with_slots, doctor_slots

router = DefaultRouter()

router.register('doctors', DoctorViewSet)
router.register('appointment_slots', AppointmentSlotViewSet)
router.register('appointments', AppointmentViewSet)
router.register('patients', PatientViewSet)
router.register('users', UserViewSet)


urlpatterns =[
path('register/', RegisterViewSet.as_view()),
path('check_auth/', check_auth),
path('me/', me),
path('doctors_with_slots/', doctors_with_slots),
path('doctor_slots/<int:doctor_id>',doctor_slots)


] + router.urls