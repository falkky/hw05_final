# Generated by Django 2.2.19 on 2022-03-02 18:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220302_2033'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='address',
            new_name='slug',
        ),
        migrations.RenameField(
            model_name='group',
            old_name='name',
            new_name='title',
        ),
    ]