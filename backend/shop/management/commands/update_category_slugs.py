from django.core.management.base import BaseCommand
from shop.models import Category
from shop.utils import cyrillic_slugify


class Command(BaseCommand):
    help = 'Обновляет slug\'и категорий на иерархические (parent-slug--child-slug)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать изменения без сохранения в БД',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('РЕЖИМ ПРОВЕРКИ (dry-run). Изменения не будут сохранены.\n'))
        else:
            self.stdout.write(self.style.WARNING('Обновление slug\'ов категорий...\n'))

        # Получаем все категории, начиная с корневых
        updated_count = 0
        processed_ids = set()
        
        # Сначала обрабатываем корневые категории (без parent)
        root_categories = Category.objects.filter(parent__isnull=True).order_by('id')
        
        for category in root_categories:
            self._update_category_slug(category, dry_run, processed_ids)
            updated_count += 1
            processed_ids.add(category.pk)
        
        # Затем обрабатываем дочерние категории по уровням вложенности
        max_level = 10
        for level in range(1, max_level + 1):
            # Находим категории, которые еще не обработаны и имеют обработанных родителей
            categories_to_process = Category.objects.filter(
                parent__isnull=False,
                parent__pk__in=processed_ids
            ).exclude(
                pk__in=processed_ids
            ).order_by('id')
            
            if not categories_to_process.exists():
                break
            
            for category in categories_to_process:
                self._update_category_slug(category, dry_run, processed_ids)
                updated_count += 1
                processed_ids.add(category.pk)
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\nПроверка завершена. Будет обновлено: {updated_count} категорий'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nОбновлено slug\'ов: {updated_count}'))

    def _update_category_slug(self, category, dry_run, processed_ids):
        """Обновляет slug для одной категории"""
        old_slug = category.slug
        
        # Генерируем новый slug - всегда только название категории (короткий)
        new_slug = cyrillic_slugify(category.name)
        
        # Проверяем уникальность только в контексте parent
        counter = 1
        base_slug = new_slug
        
        # Для корневых категорий проверяем уникальность глобально
        if category.parent is None:
            while Category.objects.filter(slug=new_slug, parent__isnull=True).exclude(pk=category.pk).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
        else:
            # Убеждаемся, что parent уже обработан
            if category.parent.pk not in processed_ids:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Пропущена {category.name} (parent не обработан): {old_slug}"
                    )
                )
                return
            
            # Для подкатегорий проверяем уникальность только среди категорий с тем же parent
            while Category.objects.filter(slug=new_slug, parent=category.parent).exclude(pk=category.pk).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
        
        if old_slug != new_slug:
            parent_info = f" (parent: {category.parent.name})" if category.parent else " (корневая)"
            self.stdout.write(
                f"  {category.name}{parent_info}:\n"
                f"    Старый: {old_slug}\n"
                f"    Новый:  {new_slug}\n"
            )
            
            if not dry_run:
                # Используем update для избежания вызова save() и рекурсии
                Category.objects.filter(pk=category.pk).update(slug=new_slug)

