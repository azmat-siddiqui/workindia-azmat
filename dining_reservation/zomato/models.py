from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six


class Token(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=40, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key

class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )

token_generator = TokenGenerator()

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance, key=token_generator.make_token(instance))


class DiningPlace(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone_no = models.CharField(max_length=13)
    website = models.URLField()
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return self.name

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dining_place = models.ForeignKey(DiningPlace, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.dining_place.name} - {self.start_time}"


