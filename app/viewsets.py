from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import viewsets, permissions, serializers, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.models import Patient, Doctor, AppointmentSlots, Appointment
from app.permissions import IsAdminStaff, IsOwnerOnly
from app.serializers import PatientSerializer, DoctorSerializer, AppointmentSerializer, AppointmentSlotsSerializer, \
    UserSerializer, RegisterSerializer
from django.db import transaction
def home(request):
    return HttpResponse("Hello World")
class DoctorViewSet(viewsets.ModelViewSet):

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


    def get_permissions(self):

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminStaff()]

        return [permissions.IsAuthenticated()]




class AppointmentSlotViewSet(viewsets.ModelViewSet):


    serializer_class = AppointmentSlotsSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AppointmentSlots.objects.all()

    def get_queryset(self):

        # admin sees all
        if self.request.user.is_staff:
            return AppointmentSlots.objects.all()

        # user sees only appointment slots with doctors allocated
        return AppointmentSlots.objects.filter(
            doctor__isnull=False

        )

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            with transaction.atomic():

               serializer.save(is_booked=False, doctor= serializer.validated_data["doctor"])
            return
        else:
            # get patient
            patient = Patient.objects.filter(
                user=self.request.user
            ).first()


            if not patient:
                raise serializers.ValidationError(
                    "Patient profile not found"
                )
            with transaction.atomic():
                # check BEFORE saving anything
                if Appointment.objects.filter(
                        patient=patient,
                        slot__date=serializer.validated_data["date"],
                        slot__start_time__lt=serializer.validated_data["end_time"],
                        slot__end_time__gt=serializer.validated_data["start_time"]
                ).exists():
                    raise serializers.ValidationError(
                        "Overlapping appointment exists"
                    )
                # create appointment slot
                slot = serializer.save(
                    doctor=None,
                    is_booked=False
                )


                # create appointment
                Appointment.objects.create(
                    patient=patient,
                    slot=slot,
                    status='pending'
                )

    def perform_update(self, serializer):
        user = self.request.user

        if user.is_staff:
            serializer.save()

            return

        # user restriction
        allowed_fields = {"is_booked"}

        for field in serializer.validated_data.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(
                    f"You cannot update '{field}'"
                )

        serializer.save()
        Appointment.objects.create(
            patient=Patient.objects.filter(user=user).first(),
            slot=serializer.instance,
            status='confirmed'
        )




class AppointmentViewSet(viewsets.ModelViewSet):

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Appointment.objects.all()

    def get_queryset(self):

        queryset = Appointment.objects.all()

        if not self.request.user.is_staff:
            return queryset.filter(patient__user=self.request.user)

        # admin filtering
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset
    # Create appointment
    def perform_create(self, serializer):

        # Admin create new appointment
        if self.request.user.is_staff:
            slot = serializer.validated_data.get('slot')
            if not slot:
                raise serializers.ValidationError("Slot not found")
            elif  slot.doctor is None:
                raise serializers.ValidationError("This slot is not valid to assign")

            with transaction.atomic():
                slot = AppointmentSlots.objects.select_for_update().get(id=slot.id)
                slot.is_booked = True
                slot.save()
                serializer.save(status='confirmed')
            return

        #  Patient book a slot
        patient = Patient.objects.filter(user=self.request.user).first()
        if not patient:
            raise serializers.ValidationError("Patient profile not found")

        # Get slot from validated data (outside transaction)
        slot = serializer.validated_data.get('slot')
        if not slot:
            raise serializers.ValidationError("Slot not found")

        with transaction.atomic():
            # Fetch slot from database with lock to prevent race conditions
            # Use slot.id from the object we got above
            slot = AppointmentSlots.objects.select_for_update().get(id=slot.id)

            # Prevent double booking
            if slot.is_booked:
                raise serializers.ValidationError("This slot is already booked")

            # Mark slot booked
            slot.is_booked = True
            slot.save()

            # Create appointment
            serializer.save(patient=patient, status='confirmed', slot=slot)

    # delete appointment
    def perform_destroy(self, instance):

        slot = instance.slot
        # Free slot if slot is allocated doctors
        if slot.doctor is not None:

            slot.is_booked = False
            slot.save()
        # delete slot if doctor is not allocated to slot
        else:
           slot.delete()

        instance.delete()

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Patient.objects.all()
        return Patient.objects.filter(user=self.request.user)


    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
            return
        user = self.request.user
        serializer.save(user=user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return None




class RegisterViewSet(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    return Response({"valid": True})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user

    return Response({
        "id": user.id,
        "username": user.username,
        "is_staff": user.is_staff
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctors_with_slots(request):

    doctors = Doctor.objects.all()

    result = []

    for doctor in doctors:

        slots = AppointmentSlots.objects.filter(doctor=doctor, is_booked=False)

        grouped = defaultdict(list)

        for slot in slots:
            grouped[str(slot.date)].append({
                "id": slot.id,
                "start_time": slot.start_time,
                "end_time": slot.end_time
            })

        result.append({
            "doctor": {
                "id": doctor.id,
                "firstName": doctor.firstName,
                "lastName": doctor.lastName,
                "speciality": doctor.speciality
            },
            "grouped_slots": grouped
        })

    return Response(result)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_slots(request,doctor_id):
    result = []
    doctor = Doctor.objects.get(id=doctor_id)
    slots = AppointmentSlots.objects.filter(doctor=doctor, is_booked=False)

    grouped = defaultdict(list)

    for slot in slots:

        grouped[str(slot.date)].append({
            "id": slot.id,
            "start_time": slot.start_time,
            "end_time": slot.end_time
        })
    result.append({
        "doctor": {
            "id": doctor.id,
            "firstName": doctor.firstName,
            "lastName": doctor.lastName,
            "speciality": doctor.speciality
        },
        "grouped_slots": grouped
    })
    return Response(result)

