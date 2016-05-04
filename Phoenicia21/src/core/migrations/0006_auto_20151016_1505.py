# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_operacjasalda'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uzytkownik',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='uzytkownik',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
    ]
