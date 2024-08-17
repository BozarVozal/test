from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from product.courses.models import Course
from product.users.models import Subscription, Balance


def make_payment(request):
    """Функция для обработки платежа."""
    user = request.user
    course_id = request.data.get('course_id')
    course = get_object_or_404(Course, id=course_id)
    balance = get_object_or_404(Balance, user=user)

    if balance.amount < course.price:
        return Response(
            {"detail": "Недостаточно бонусов для покупки курса."},
            status=status.HTTP_400_BAD_REQUEST
        )

    balance.amount -= course.price
    balance.save()

    subscription, created = Subscription.objects.get_or_create(
        user=user,
        course=course,
        defaults={'access_granted': True}
    )

    if not created:
        subscription.access_granted = True
        subscription.save()

    return Response(
        {"detail": "Оплата успешно выполнена."},
        status=status.HTTP_200_OK
    )


class IsStudentOrIsAdmin(BasePermission):
    def has_permission(self, request, view):
        """Проверка прав доступа на уровне запроса."""
        if request.user.is_staff:
            return True
        return Subscription.objects.filter(user=request.user, course=view.kwargs.get('course_id')).exists()

    def has_object_permission(self, request, view, obj):
        """Проверка прав доступа на уровне объекта."""
        if request.user.is_staff:
            return True
        return Subscription.objects.filter(user=request.user, course=obj.course).exists()


class ReadOnlyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.method in SAFE_METHODS
