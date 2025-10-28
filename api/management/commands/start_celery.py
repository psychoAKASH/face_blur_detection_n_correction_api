from django.core.management.base import BaseCommand
import subprocess
import sys


class Command(BaseCommand):
    help = 'Start Celery worker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--concurrency',
            type=int,
            default=2,
            help='Number of concurrent workers'
        )

    def handle(self, *args, **options):
        concurrency = options['concurrency']
        self.stdout.write(self.style.SUCCESS('Starting Celery worker...'))

        try:
            subprocess.call([
                'celery', '-A', 'face_blur_api', 'worker',
                '--loglevel=info',
                f'--concurrency={concurrency}'
            ])
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Celery worker stopped'))
            sys.exit(0)