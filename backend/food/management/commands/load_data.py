import json
import os

from django.core.management.base import BaseCommand

from food.models import Ingredient

JSON_PATH = os.path.join('/app/data')
MODEL = Ingredient


class Command(BaseCommand):
    """Пользовательская команда Django для импорта данных из json в БД."""

    def handle(self, *args, **kwargs):
        file_path = os.path.join(JSON_PATH, 'ingredients.json')
        error_occurred = False
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                objects_to_create = [MODEL(**item) for item in data]

                MODEL.objects.bulk_create(
                    objects_to_create, ignore_conflicts=True
                )

                self.stdout.write(
                    self.style.SUCCESS('DATA SUCCESSFULLY LOADED')
                )
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Error processing file {file_path}: {error}'
                )
            )
            error_occurred = True

            if error_occurred:
                self.stdout.write(
                    self.style.ERROR('FAILED TO LOAD DATA')
                )
