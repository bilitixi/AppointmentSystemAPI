from django.contrib import admin

from app.models import Patient, Doctor, AppointmentSlots, Appointment

# Register your models here.
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(AppointmentSlots)
admin.site.register(Appointment)