from django.core.management.base import BaseCommand
from core.models import Customer, Loan
from core.tasks import ingest_customer_data, ingest_loan_data
from django.db import connection


def reset_customer_id_sequence():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence('core_customer', 'customer_id'), COALESCE(MAX(customer_id), 1), MAX(customer_id) IS NOT NULL) FROM core_customer;"
        )

class Command(BaseCommand):
    help = "Ingests initial customer and loan data from Excel files"

    def handle(self, *args, **kwargs):
        if Customer.objects.exists():
            self.stdout.write(self.style.WARNING("Customer data already exists."))
        else:
            self.stdout.write(self.style.SUCCESS("Starting customer data ingestion..."))
            ingest_customer_data("data/customer_data.xlsx")  # Synchronous call
            self.stdout.write(self.style.SUCCESS("Customer data ingestion complete."))
            reset_customer_id_sequence()  # Ensure sequence is correct

        if Loan.objects.exists():
            self.stdout.write(self.style.WARNING("Loan data already exists."))
        else:
            self.stdout.write(self.style.SUCCESS("Starting loan data ingestion..."))
            ingest_loan_data("data/loan_data.xlsx")  # Synchronous call
            self.stdout.write(self.style.SUCCESS("Loan data ingestion complete."))
