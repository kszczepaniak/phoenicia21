# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20151016_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='uzytkownik',
            name='is_staff',
            field=models.BooleanField(default=False),
        ),
    ]
