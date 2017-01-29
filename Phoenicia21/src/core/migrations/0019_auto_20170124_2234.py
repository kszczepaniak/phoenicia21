# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_dokument_wyzywienie_zbiorka'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dokument',
            name='wyzywienie_zbiorka',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
