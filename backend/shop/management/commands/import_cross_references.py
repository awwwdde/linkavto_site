import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from shop.models import Product, ProductCrossReference, normalize_article_number


class Command(BaseCommand):
    help = (
        "Import product cross references from CSV/XLSX. "
        "Columns: product_article, cross_article, brand, relation_type, analog_article, comment."
    )

    def add_arguments(self, parser):
        parser.add_argument('file_path')
        parser.add_argument('--delimiter', default=';')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        file_path = Path(options['file_path'])
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        rows = self._read_rows(file_path, options['delimiter'])
        created = 0
        updated = 0
        skipped = 0

        for row_number, row in enumerate(rows, start=2):
            product_article = self._get_value(row, 'product_article', 'part_number', 'product_part_number')
            cross_article = self._get_value(row, 'cross_article', 'article_number', 'cross_number')

            if not product_article or not cross_article:
                skipped += 1
                self.stderr.write(f"Row {row_number}: missing product_article or cross_article")
                continue

            products = Product.objects.filter(
                normalized_part_number=normalize_article_number(product_article)
            )
            if not products.exists():
                skipped += 1
                self.stderr.write(f"Row {row_number}: product not found for article {product_article}")
                continue

            analog_product = self._find_analog_product(row)
            brand = self._get_value(row, 'brand', 'manufacturer') or ''
            relation_type = self._get_value(row, 'relation_type', 'type') or 'cross'
            comment = self._get_value(row, 'comment', 'note') or ''

            if relation_type not in dict(ProductCrossReference.RELATION_TYPES):
                skipped += 1
                self.stderr.write(f"Row {row_number}: unknown relation_type {relation_type}")
                continue

            for product in products:
                defaults = {
                    'article_number': cross_article,
                    'analog_product': analog_product,
                    'comment': comment,
                    'is_active': True,
                }

                if options['dry_run']:
                    created += 1
                    continue

                _, was_created = ProductCrossReference.objects.update_or_create(
                    product=product,
                    normalized_article=normalize_article_number(cross_article),
                    brand=brand,
                    relation_type=relation_type,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Cross references import finished. Created: {created}, updated: {updated}, skipped: {skipped}"
        ))

    def _read_rows(self, file_path, delimiter):
        suffix = file_path.suffix.lower()
        if suffix in {'.xlsx', '.xls'}:
            try:
                import pandas as pd
            except ImportError as exc:
                raise CommandError("pandas is required for XLS/XLSX import") from exc
            return pd.read_excel(file_path).fillna('').to_dict('records')

        with file_path.open('r', encoding='utf-8-sig', newline='') as source:
            return list(csv.DictReader(source, delimiter=delimiter))

    def _find_analog_product(self, row):
        analog_id = self._get_value(row, 'analog_product_id')
        if analog_id:
            return Product.objects.filter(id=analog_id).first()

        analog_article = self._get_value(row, 'analog_article', 'analog_part_number')
        if not analog_article:
            return None

        return Product.objects.filter(
            normalized_part_number=normalize_article_number(analog_article)
        ).first()

    @staticmethod
    def _get_value(row, *keys):
        for key in keys:
            value = row.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ''
