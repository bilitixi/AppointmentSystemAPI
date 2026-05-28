from django.urls import path
from rest_framework.routers import DefaultRouter
from app.viewsets import DoctorViewSet, AppointmentSlotViewSet, AppointmentViewSet, PatientViewSet, UserViewSet, \
    RegisterViewSet, check_auth, me, getdoctorappointment

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
path('getdoctorappointment/<int:doctor_id>/', getdoctorappointment),

] + router.urls