from django.contrib.auth.models import User
from rest_framework import serializers
from app.models import Patient, Doctor, AppointmentSlots, Appointment

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'
class AppointmentSlotsSerializer(serializers.ModelSerializer):

    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = AppointmentSlots
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'date',
            'start_time',
            'end_time',
            'is_booked',
            'speciality'
        ]

    def get_doctor_name(self, obj):
        if obj.doctor:
            return str(obj.doctor)
        return None
class AppointmentSerializer(serializers.ModelSerializer):

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    slot_info = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'patient_name',
            'slot',
            'slot_info',
            'doctor_name',
            'status',
            'created_at',
            'updated_at'
        ]
    def get_patient_name(self, obj):
        return str(obj.patient)


    def get_doctor_name(self, obj):
        return str(obj.slot.doctor) if obj.slot and obj.slot.doctor else None


    def get_slot_info(self, obj):
        slot = obj.slot
        return {
            "date": slot.date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "speciality": slot.speciality
        }
class UserSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        xtra_kwargs = {'password': {'write_only': True, 'required': True}}
    def create(self, validated_data): # overwrite create function of serializer
        user = User.objects.create_user(**validated_data)
        return user