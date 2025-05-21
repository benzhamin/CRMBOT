from django.core.management.base import BaseCommand
from crm.bot import main  # Функсияи main аз bot.py

class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **kwargs):
        import asyncio
        asyncio.run(main())