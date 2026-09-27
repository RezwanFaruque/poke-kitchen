from django.core.management.base import BaseCommand

from kitchines.vectorstore import is_enabled, sync_all_orders


class Command(BaseCommand):
    help = 'Embed existing kitchen orders into the local vector store.'

    def handle(self, *args, **options):
        if not is_enabled():
            self.stderr.write('Vector store is disabled. Set VECTOR_STORE_ENABLED=True.')
            return

        count = sync_all_orders()
        self.stdout.write(self.style.SUCCESS(f'Synced {count} order(s) to the vector store.'))
