from PIL import UnidentifiedImageError
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from easy_thumbnails.exceptions import EasyThumbnailsError
from easy_thumbnails.files import get_thumbnailer

# User = get_user_model()
from src.models.models import File


@receiver(post_delete, sender=File)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete()

    if instance.thumbnail:
        instance.thumbnail.delete()


@receiver(post_save, sender=File)
def generate_thumbnail(sender, instance=None, created=False, **kwargs):
    # avoid recursion
    if created is False:
        return

    thumbnailer = get_thumbnailer(instance.file.name, relative_name='thumbnail')
    try:
        thumbnail = thumbnailer.get_thumbnail({'size': File.THUMBNAIL_SIZE}, save=False)
    except (UnidentifiedImageError, EasyThumbnailsError):
        return
    else:
        instance.thumbnail.save(name=f'small_{instance.file.name}', content=thumbnail)
