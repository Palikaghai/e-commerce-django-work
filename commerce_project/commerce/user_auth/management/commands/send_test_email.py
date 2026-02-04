from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP settings. Usage: manage.py send_test_email --to you@example.com'

    def add_arguments(self, parser):
        parser.add_argument('--to', required=True, help='Destination email address')
        parser.add_argument('--subject', default='Test email from Glow & Beauty')
        parser.add_argument('--message', default='This is a test email sent from the Django app to verify SMTP configuration.')

    def handle(self, *args, **options):
        to = options['to']
        subject = options['subject']
        message = options['message']
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
            self.stdout.write(self.style.SUCCESS(f"Email successfully sent to {to}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
