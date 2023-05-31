import json

from django.db import migrations

TAGS = [
    {'name': 'Завтрак', 'color': '#fff000', 'slug': 'zavtrak'},
    {'name': 'Обед', 'color': '#fe00ac', 'slug': 'obed'},
    {'name': 'Ужин', 'color': '#10ff01', 'slug': 'uzhin'},
    {'name': 'Полезное', 'color': '#ff00f3', 'slug': 'pp'},
    {'name': 'Мясо', 'color': '#90', 'slug': 'meat'},
    {'name': 'Овощи', 'color': '#ff9efa', 'slug': 'vegan'},
]


def add_tag(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")
    tags = [Tag(**tag) for tag in TAGS]
    Tag.objects.bulk_create(tags)


def remove_tag(apps, schema_editor):
    Tag = apps.get_model("recipes", "Tag")
    for tag in TAGS:
        Tag.objects.get(id=tag['id']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_add_ingredients'),
    ]

    operations = [
        migrations.RunPython(
            add_tag,
            remove_tag,
        )
    ]
