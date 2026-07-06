from django.urls import path
from rest_framework.routers import DefaultRouter
from app.viewsets import DoctorViewSet, AppointmentSlotViewSet, AppointmentViewSet, PatientViewSet, UserViewSet, \
    RegisterViewSet, check_auth, me, doctors_with_slots, doctor_slots, admin_book_appointment_for_patient, \
    create_patient, logout, verify_email, resend_verification_email

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
path('doctor_slots/<int:doctor_id>',doctor_slots),
path('book_appointment_for_patient/<int:patientID>',admin_book_appointment_for_patient),
path('createpatients/', create_patient),
path('logout/', logout),
path('verify_email/<str:token>/', verify_email),
path('resend_verification_email/', resend_verification_email),

] + router.urls