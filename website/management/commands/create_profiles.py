from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from website.models import Profile


class Command(BaseCommand):
    help = 'Crea perfiles para usuarios que no tienen uno'

    def handle(self, *args, **kwargs):
        users_without_profile = []

        for user in User.objects.all():
            try:
                # Intenta acceder al perfil
                _ = user.profile
            except Profile.DoesNotExist:
                # Si no existe, créalo
                Profile.objects.create(user=user)
                users_without_profile.append(user.username)

        if users_without_profile:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Perfiles creados para: {", ".join(users_without_profile)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Todos los usuarios ya tienen perfil')
            )
