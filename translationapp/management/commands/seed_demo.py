from django.core.management.base import BaseCommand
from translationapp.models import SampleModel


class Command(BaseCommand):
    help = 'Add one fictional multilingual content record; creates no user accounts.'

    def handle(self, *args, **options):
        _, created = SampleModel.objects.get_or_create(
            title={'en': 'A world of stories', 'fr': 'Un monde de récits', 'ar': 'عالم من القصص'},
            defaults={
                'article': {
                    'en': 'Make every reader feel at home. Write once, then shape your message for each language.',
                    'fr': 'Offrez à chaque lecteur un accueil chaleureux. Adaptez votre message à chaque langue.',
                    'ar': 'اجعل كل قارئ يشعر بأنه في بيته. اكتب رسالتك ثم صغها لكل لغة.',
                },
                'author': {'name': 'Sample editorial team'},
            },
        )
        self.stdout.write(self.style.SUCCESS('Demo content created.' if created else 'Demo content already exists.'))
