from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token

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
            'speciality',

        ]

    def get_doctor_name(self, obj):
        if obj.doctor:
            return str(obj.doctor)
        return None


    def validate(self, attrs):
        # Check for overlapping time slots for the same doctor on the same date
        doctor = attrs.get('doctor')
        date = attrs.get('date')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        # Only validate if BOTH are being updated
        if start_time is not None and end_time is not None:
            # Check if start_time is before end_time
            if start_time >= end_time:
                raise serializers.ValidationError({
                    'start_time': 'Start time must be before end time.',
                    'end_time': 'End time must be after start time.'
                })

        # validate overlap if doctor exists
        if doctor is None:
            return attrs



        # Find existing slots for the same doctor and date
        existing_slots = AppointmentSlots.objects.filter(
            doctor=doctor,
            date=date
        )

        # Exclude current instance if we're updating
        if self.instance:
            existing_slots = existing_slots.exclude(pk=self.instance.pk)

        # Check for overlaps
        for slot in existing_slots:
            # Slots overlap if: start1 < end2 AND start2 < end1
            if start_time < slot.end_time and slot.start_time < end_time:
                raise serializers.ValidationError({
                    'start_time': f'Time slot overlaps with existing slot from {slot.start_time} to {slot.end_time}.',
                    'end_time': f'Time slot overlaps with existing slot from {slot.start_time} to {slot.end_time}.'
                })

        return attrs


class AppointmentSerializer(serializers.ModelSerializer):

    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    slot_info = serializers.SerializerMethodField()
    doctorID = serializers.SerializerMethodField()

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
            'updated_at',
            'doctorID'
        ]
    def get_doctorID(self, obj):
        if obj.slot and obj.slot.doctor:
            return obj.slot.doctor.id
        return None
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
            "speciality": slot.speciality,
            "appointmentslotID": slot.id
        }
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}
    def create(self, validated_data): # overwrite create function of serializer
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user) # create token
        return user
class RegisterSerializer(serializers.ModelSerializer):
    patient_firstName = serializers.CharField(write_only=True)
    patient_lastName = serializers.CharField(write_only=True)
    patient_phone = serializers.CharField(write_only=True)
    patient_date_of_birth = serializers.DateField(write_only=True)
    patient_address = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'patient_firstName',
            'patient_lastName',
            'patient_phone',
            'patient_date_of_birth',
            'patient_address'
        ]

        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):

        patient_firstName = validated_data.pop('patient_firstName')
        patient_lastName = validated_data.pop('patient_lastName')
        patient_phone = validated_data.pop('patient_phone')
        patient_date_of_birth = validated_data.pop('patient_date_of_birth')
        patient_address = validated_data.pop('patient_address')

        user = User.objects.create_user(username = validated_data['username'], password = validated_data['password'],email = validated_data['username'],first_name = patient_firstName, last_name = patient_lastName)
        Token.objects.create(user=user)  # create token
        Patient.objects.create(
            user=user,
            firstName=patient_firstName,
            lastName=patient_lastName,
            phone=patient_phone,
            date_of_birth=patient_date_of_birth,
            address=patient_address
        )

        return user