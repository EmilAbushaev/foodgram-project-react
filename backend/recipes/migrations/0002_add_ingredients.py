import json

from django.db import migrations

INGREDIENTS = []


def make_migration(apps, schema_editor):
    global INGREDIENTS
    file = open('ingredients.json', encoding='UTF-8')
    data = json.load(file)
    for ingredient in data:
        data_dict = {
            'name': ingredient['name'],
            'measurement_unit': ingredient['measurement_unit']
        }
        if data_dict not in INGREDIENTS:
            INGREDIENTS.append(data_dict)
    return INGREDIENTS


def add_ingredient(apps, schema_editor):
    Ingredient = apps.get_model("recipes", "Ingredient")
    ingredients = [
        Ingredient(
            name=ingredient['name'],
            measurement_unit=ingredient['measurement_unit']
        )
        for ingredient in INGREDIENTS
    ]
    Ingredient.objects.bulk_create(ingredients)


def remove_ingredient(apps, schema_editor):
    Ingredient = apps.get_model("recipes", "Ingredient")
    for ingredient in INGREDIENTS:
        Ingredient.objects.get(id=ingredient['id']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            make_migration,
        ),
        migrations.RunPython(
            add_ingredient,
            remove_ingredient,
        )
    ]
