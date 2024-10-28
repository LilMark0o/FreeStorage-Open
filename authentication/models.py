from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Default value for storage size in bytes
    storageSize = models.IntegerField(default=1024**3 * 50)  # 50 GB
    sizePerFile = models.IntegerField(default=1024**2 * 25)  # 50 MB
    authenticated = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = UserProfile.objects.get(pk=self.pk)
            # Check if authenticated was changed to True
            if not old_instance.authenticated and self.authenticated:
                # Change storage size and size per file when authenticated becomes True
                if old_instance.storageSize < 1024**3 * 100:
                    self.storageSize = 1024**3 * 100
                if old_instance.sizePerFile < 1024**2 * 50:
                    self.sizePerFile = 1024**2 * 50
            if old_instance.authenticated and (not self.authenticated):
                # Change storage size and size per file when authenticated becomes False
                if old_instance.storageSize > 1024**3 * 50:
                    self.storageSize = 1024**3 * 50
                if old_instance.sizePerFile > 1024**2 * 25:
                    self.sizePerFile = 1024**2 * 25
        super().save(*args, **kwargs)


# Signal to create or update UserProfile when User is created or updated


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()
