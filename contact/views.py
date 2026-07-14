from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save()
            return Response({
                'success': True,
                'message': 'Your message has been sent. We will get back to you soon.'
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminContactView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        messages = ContactMessage.objects.all()
        status_filter = request.query_params.get('status', '')
        if status_filter:
            messages = messages.filter(status=status_filter)
        serializer = ContactMessageSerializer(messages, many=True)
        return Response({
            'success': True,
            'count': messages.count(),
            'messages': serializer.data
        })

    def patch(self, request, pk):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            message = ContactMessage.objects.get(pk=pk)
            new_status = request.data.get('status', 'read')
            message.status = new_status
            message.save()
            return Response({'success': True, 'message': 'Contact message status updated.'})
        except ContactMessage.DoesNotExist:
            return Response({'detail': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)
