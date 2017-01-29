# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20170124_2234'),
    ]

    operations = [
        migrations.AddField(
            model_name='uzytkownik',
            name='is_skarbnik',
            field=models.BooleanField(default=False),
        ),
    ]
