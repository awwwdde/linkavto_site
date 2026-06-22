#!/usr/bin/env python3
"""
Скрипт для обновления slug категорий с кириллическими названиями
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings.development')
django.setup()

from shop.models import Category
from shop.utils import cyrillic_slugify

def update_slugs_cyrillic():
    """Обновляет slug для всех категорий с кириллическими названиями"""
    
    print("=== ОБНОВЛЕНИЕ SLUG КАТЕГОРИЙ (КИРИЛЛИЦА) ===")
    
    # Обновляем корневые категории
    root_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    
    for category in root_categories:
        old_slug = category.slug
        new_slug = cyrillic_slugify(category.name)
        
        # Проверяем уникальность
        counter = 1
        original_slug = new_slug
        while Category.objects.filter(slug=new_slug).exclude(pk=category.pk).exists():
            new_slug = f"{original_slug}-{counter}"
            counter += 1
        
        category.slug = new_slug
        category.save()
        print(f"✓ {category.name}: '{old_slug}' -> '{new_slug}'")
    
    # Обновляем подкатегории
    subcategories = Category.objects.filter(parent__isnull=False, is_active=True)
    
    for category in subcategories:
        old_slug = category.slug
        new_slug = cyrillic_slugify(category.name)
        
        # Проверяем уникальность
        counter = 1
        original_slug = new_slug
        while Category.objects.filter(slug=new_slug).exclude(pk=category.pk).exists():
            new_slug = f"{original_slug}-{counter}"
            counter += 1
        
        category.slug = new_slug
        category.save()
        print(f"  ✓ {category.name}: '{old_slug}' -> '{new_slug}'")
    
    print("\n=== ПРОВЕРКА РЕЗУЛЬТАТА ===")
    for cat in Category.objects.filter(parent__isnull=True, is_active=True):
        print(f"- {cat.name}: slug=\"{cat.slug}\"")

if __name__ == '__main__':
    update_slugs_cyrillic()
