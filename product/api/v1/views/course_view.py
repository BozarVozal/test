from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from product.api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin
from product.api.v1.serializers.course_serializer import (CourseSerializer, CreateCourseSerializer,
                                                          CreateGroupSerializer, CreateLessonSerializer,
                                                          GroupSerializer, LessonSerializer)
from product.api.v1.serializers.user_serializer import SubscriptionSerializer
from product.courses.models import Course, Group, Lesson
from product.users.models import Subscription, Balance


class LessonViewSet(viewsets.ModelViewSet):
    """Уроки."""

    permission_classes = (IsStudentOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.lessons.all()


class GroupViewSet(viewsets.ModelViewSet):
    """Группы."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.groups.all()


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def pay(self, request, pk):

        """Покупка доступа к курсу (подписка на курс)."""

        course = get_object_or_404(Course, pk=pk)
        user = request.user
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

        data = SubscriptionSerializer(subscription).data

        return Response(
            data=data,
            status=status.HTTP_201_CREATED
        )
