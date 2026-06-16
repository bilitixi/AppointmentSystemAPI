from collections import defaultdict
from datetime import date, timedelta, datetime

import pandas as pd
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
            appointmentSlot = serializer.instance
            appointment = Appointment.objects.filter(slot=appointmentSlot).first()
            if not appointment:
                return

            if appointmentSlot.doctor:
                appointment.status = 'confirmed'
                appointment.save()
            else:
                appointment.status = 'pending'
                appointment.save()


            return

        # user restriction
        allowed_fields = {"is_booked"}

        for field in serializer.validated_data.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(
                    f"You cannot update '{field}'"
                )

        serializer.save(is_booked=True)
        Appointment.objects.create(
            patient=Patient.objects.filter(user=user).first(),
            slot=serializer.instance,
            status='confirmed'
        )




class AppointmentViewSet(viewsets.ModelViewSet):

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Appointment.objects.all()

    def get_permissions(self):

        # Staff can do everything
        if self.request.user.is_staff:
            return [permissions.IsAuthenticated()]

        # Regular users can only view and delete
        if self.action in ["list", "retrieve", "destroy"]:
            return [permissions.IsAuthenticated()]

        return [permissions.IsAdminUser()]

    def get_queryset(self):
        queryset = Appointment.objects.all()
        user = self.request.user

        #  only their own appointments
        if not user.is_staff:
            return queryset.filter(patient__user=user)

        #  can filter by patient_id
        patient_id = self.request.query_params.get('patient_id')

        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)

        return queryset
    # Create appointment
    """
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
    """
    # delete appointment
    def perform_destroy(self, instance):
        slot = instance.slot

        if slot.doctor is not None:
            slot.is_booked = False
            slot.save()
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
    def perform_destroy(self, instance):
        if self.request.user.is_staff:

            patientappointments = Appointment.objects.filter(
                patient=instance
            ).select_related("slot")

            # get slot ids
            slot_ids = [a.slot_id for a in patientappointments]

            AppointmentSlots.objects.filter(
                id__in=slot_ids
            ).update(is_booked=False)

            # delete patient
            instance.delete()
            # delete user
            user = instance.user
            user.delete()

            return
        else:
            user = self.request.user
            if user != instance.user:
                raise serializers.ValidationError("You are not allowed to delete this patient")
            user.delete()
            instance.delete()
    def perform_update(self, serializer):
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
@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_book_appointment_for_patient(request,patientID):
    selectedDoctor = Doctor.objects.get(id=request.data['doctor'])
    selectedPatient = Patient.objects.get(id=patientID)
    start_time = datetime.strptime(
        request.data['start_time'],
        "%H:%M:%S"
    ).time()

    end_time = datetime.strptime(
        request.data['end_time'],
        "%H:%M:%S"
    ).time()
    if start_time > end_time:
        return Response({"message": "Invalid time range"})
    with transaction.atomic():

        # check BEFORE saving anything
        if Appointment.objects.filter(
                patient=selectedPatient,
                slot__date=request.data["date"],
                slot__start_time__lt=end_time,
                slot__end_time__gt=start_time
        ).exists():
            raise serializers.ValidationError(
                "Overlapping appointment exists"
            )


        appointmentSLot = AppointmentSlots.objects.create(doctor=selectedDoctor,
            date=request.data['date'],
            start_time=request.data['start_time'],
            end_time=request.data['end_time'],
            is_booked=True,
            speciality= request.data['speciality']


        )



        appointment = Appointment.objects.create(
            patient=selectedPatient,
            status='confirmed',
            slot= appointmentSLot
        )

        return Response({"message": "Appointment created successfully"})


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def create_patient(request):
    names_file = request.FILES['names_file']
    excel_read = pd.read_excel(names_file)
    data = pd.DataFrame(excel_read,
                        columns=['email', 'password', 'first_name', 'last_name', 'date_of_birth', 'address'])
    usernames = data['email'].tolist()
    passwords = data['password'].tolist()
    first_names = data['first_name'].tolist()
    last_names = data['last_name'].tolist()
    DOBs = data['date_of_birth'].tolist()
    addresses = data['address'].tolist()
    for username, password, first_name, last_name, DOB, address in zip(usernames, passwords, first_names, last_names,
                                                                       DOBs, addresses):
        try:
            user = User.objects.get(username=username)
            user.delete()
            user = User(username=username, first_name=first_name, last_name=last_name, email=username)
            user.set_password(password)
            user.save()
            patient = Patient(user=user, firstName=first_name, lastName=last_name, date_of_birth=DOB,
                              address=address)
            patient.save()
        except User.DoesNotExist:
            user = User(username=username, first_name=first_name, last_name=last_name, email=username)
            user.set_password(password)
            user.save()
            patient = Patient(user=user, firstName=first_name, lastName=last_name, date_of_birth=DOB,
                              address=address)
            patient.save()
    return Response({"message": "Patients created successfully."})

@api_view(['GET'])
def logout(request):
    user = request.user
    user.auth_token.delete()
    return Response({"message": "Logout successful"}, status=200)