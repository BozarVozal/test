from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from product.users.models import Subscription
from product.courses.models import Group


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """
    Распределение нового студента в группу курса.
    """

    if created:
        course = instance.course
        # Найти группу с наименьшим количеством студентов
        group = Group.objects.filter(course=course).annotate(student_count=Count('subscription')).order_by(
            'student_count').first()

        if group:
            # Добавить студента в найденную группу
            instance.group = group
            instance.save()
