from django.db import models

# Create your models here.
from django.db import models
from rest_framework import serializers


# Create your models here.
class Patient(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    address = models.CharField(max_length=255)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    def __str__(self):
        return f"{self.firstName} {self.lastName}"
class Doctor(models.Model):
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    address = models.CharField(max_length=255)
    speciality = models.CharField(max_length=255)

    def __str__(self):
        return f"Dr {self.firstName}  {self.lastName} - {self.speciality}"
class AppointmentSlots(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE,null = True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    speciality = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.doctor} - {self.date}"
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    slot = models.ForeignKey(AppointmentSlots, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.patient} - {self.slot} - {self.status} - {self.created_at}"




