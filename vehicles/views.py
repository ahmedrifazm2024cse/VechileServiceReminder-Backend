"""
Views for vehicles app
"""

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Vehicle
from .serializers import VehicleSerializer, VehicleListSerializer


class VehicleListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vehicles = Vehicle.objects.filter(owner=request.user)

        # Search
        search = request.query_params.get('search', '')
        if search:
            vehicles = vehicles.filter(
                Q(name__icontains=search) |
                Q(brand__icontains=search) |
                Q(model__icontains=search) |
                Q(registration_number__icontains=search)
            )

        # Filter
        brand = request.query_params.get('brand', '')
        if brand:
            vehicles = vehicles.filter(brand__icontains=brand)

        fuel_type = request.query_params.get('fuel_type', '')
        if fuel_type:
            vehicles = vehicles.filter(fuel_type=fuel_type)

        status_filter = request.query_params.get('status', '')
        if status_filter == 'overdue':
            vehicle_ids = [v.id for v in vehicles if v.is_overdue]
            vehicles = vehicles.filter(id__in=vehicle_ids)
        elif status_filter == 'upcoming':
            vehicle_ids = [v.id for v in vehicles if v.is_upcoming]
            vehicles = vehicles.filter(id__in=vehicle_ids)

        # Sort
        sort = request.query_params.get('sort', '-created_at')
        allowed_sorts = ['created_at', '-created_at', 'name', '-name', 'last_service_date', '-last_service_date']
        if sort in allowed_sorts:
            vehicles = vehicles.order_by(sort)

        serializer = VehicleListSerializer(vehicles, many=True, context={'request': request})
        return Response({
            'success': True,
            'count': vehicles.count(),
            'vehicles': serializer.data
        })

    def post(self, request):
        serializer = VehicleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            vehicle = serializer.save(owner=request.user)
            # Create default reminder for vehicle
            from notifications.models import Reminder
            Reminder.objects.get_or_create(
                vehicle=vehicle,
                defaults={
                    'is_enabled': False,
                    'reminder_days': [30, 15, 7, 1]
                }
            )
            return Response({
                'success': True,
                'message': 'Vehicle added successfully.',
                'vehicle': VehicleSerializer(vehicle, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VehicleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_vehicle(self, pk, user):
        try:
            if user.is_admin:
                return Vehicle.objects.get(pk=pk)
            return Vehicle.objects.get(pk=pk, owner=user)
        except Vehicle.DoesNotExist:
            return None

    def get(self, request, pk):
        vehicle = self.get_vehicle(pk, request.user)
        if not vehicle:
            return Response({'detail': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VehicleSerializer(vehicle, context={'request': request})
        return Response({'success': True, 'vehicle': serializer.data})

    def put(self, request, pk):
        vehicle = self.get_vehicle(pk, request.user)
        if not vehicle:
            return Response({'detail': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VehicleSerializer(
            vehicle, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            vehicle = serializer.save()
            return Response({
                'success': True,
                'message': 'Vehicle updated successfully.',
                'vehicle': VehicleSerializer(vehicle, context={'request': request}).data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        vehicle = self.get_vehicle(pk, request.user)
        if not vehicle:
            return Response({'detail': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)
        vehicle.delete()
        return Response({'success': True, 'message': 'Vehicle deleted successfully.'})


class AdminVehiclesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        vehicles = Vehicle.objects.all().select_related('owner')
        search = request.query_params.get('search', '')
        if search:
            vehicles = vehicles.filter(
                Q(name__icontains=search) |
                Q(registration_number__icontains=search) |
                Q(brand__icontains=search) |
                Q(owner__email__icontains=search)
            )

        serializer = VehicleSerializer(vehicles, many=True, context={'request': request})
        return Response({
            'success': True,
            'count': vehicles.count(),
            'vehicles': serializer.data
        })

    def delete(self, request, pk):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            vehicle = Vehicle.objects.get(pk=pk)
            vehicle.delete()
            return Response({'success': True, 'message': 'Vehicle deleted successfully.'})
        except Vehicle.DoesNotExist:
            return Response({'detail': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)
