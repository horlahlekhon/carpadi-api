# Generated by Django 3.2.4 on 2022-03-12 19:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='carbrand',
            unique_together={('name', 'model', 'year')},
        ),
    ]
