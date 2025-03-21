from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Sets up the default site'

    def handle(self, *args, **kwargs):
        # Delete any existing sites
        Site.objects.all().delete()
        
        # Create the default site
        site = Site.objects.create(
            id=1,
            domain='127.0.0.1:8000',
            name='localhost'
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created site: {site}')) 