from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Activa un usuario y marca su email como verificado'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario a activar')

    def handle(self, *args, **kwargs):
        username = kwargs['username']

        try:
            user = User.objects.get(username=username)
            user.is_active = True
            user.save()

            user.profile.email_verified = True
            user.profile.verification_token = None
            user.profile.save()

            self.stdout.write(
                self.style.SUCCESS(f'Usuario "{username}" activado exitosamente')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario "{username}" no encontrado')
            )
