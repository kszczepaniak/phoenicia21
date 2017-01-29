# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_zaliczka_hufiec'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokument',
            name='wyzywienie_zbiorka',
            field=models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True),
        ),
    ]
