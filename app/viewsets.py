from rest_framework import viewsets, permissions, serializers
from rest_framework.permissions import AllowAny

from app.models import Patient, Doctor, AppointmentSlots, Appointment
from app.permissions import IsAdminStaff, IsOwnerOnly
from app.serializers import PatientSerializer, DoctorSerializer, AppointmentSerializer, AppointmentSlotsSerializer


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

        # user sees only own requested slots
        return AppointmentSlots.objects.filter(
            appointment__patient__user=self.request.user
        )

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
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
            serializer.save()
            return

        #  Get logged in patient
        patient = Patient.objects.filter(
            user=self.request.user
        ).first()

        if not patient:
            raise serializers.ValidationError(
                "Patient profile not found"
            )

        # Get selected slot
        slot = serializer.validated_data.get('slot')

        if not slot:
            raise serializers.ValidationError(
                "Slot not found"
            )

        # Prevent double booking
        if slot.is_booked:
            raise serializers.ValidationError(
                "This slot is already booked"
            )

        # Mark slot booked
        slot.is_booked = True
        slot.save()

        # Create appointment
        serializer.save(
            patient=patient,
            status='confirmed'
        )


    # delete appointment
    def perform_destroy(self, instance):
        # Free slot
        if instance.slot is not None:
            slot = instance.slot
            slot.is_booked = False
            slot.save()

        instance.delete()

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]


    def get_permissions(self):
        # OWNER delete rule first
        if self.action == 'destroy':
            return [permissions.IsAuthenticated(), IsOwnerOnly()]

        # ADMIN write rules
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAdminStaff()]

        # default read access
        return [permissions.IsAuthenticated()]