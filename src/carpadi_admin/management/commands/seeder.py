from django.core.management.base import BaseCommand

from src.common.seeder import PadiSeeder


class Command(BaseCommand):
    help = 'Seeds the database.'

    # def add_arguments(self, parser):
    #     parser.add_argument('--count',
    #         default=1,
    #         type=int,
    #         help='The number of fake data per model to create.')

    def handle(self, *args, **options):
        PadiSeeder(self).seed()
