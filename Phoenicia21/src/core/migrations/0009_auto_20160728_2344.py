# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20160728_2115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faktura',
            name='data_wystawienia',
            field=models.DateField(null=True, blank=True),
        ),
    ]
