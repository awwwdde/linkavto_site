from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
import logging

logger = logging.getLogger(__name__)


# Отключен - профиль создается только при успешной регистрации через форму
# @receiver(post_save, sender=User)
# def create_or_update_profile(sender, instance, created, **kwargs):
#     """
#     Создает или обновляет профиль пользователя при сохранении модели User.
#     Логирует ошибки при создании профиля.
#     """
#     try:
#         if created:
#             Profile.objects.create(user=instance)
#             logger.info(f"Создан новый профиль для пользователя {instance.username}")
#         else:
#             # Обновляем связанный профиль, если он существует
#             if hasattr(instance, 'profile'):
#                 instance.profile.save()
#                 logger.debug(f"Профиль пользователя {instance.username} обновлен")
#     except Exception as e:
#         logger.error(f"Ошибка при создании/обновлении профиля для {instance.username}: {str(e)}")


@receiver(pre_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    """
    Удаляет связанный профиль при удалении пользователя.
    Обратите внимание: фото профиля удаляется через модель Profile (метод delete)
    """
    try:
        if hasattr(instance, 'profile'):
            instance.profile.delete()
            logger.info(f"Профиль пользователя {instance.username} удален")
    except Exception as e:
        logger.error(f"Ошибка при удалении профиля пользователя {instance.username}: {str(e)}")
