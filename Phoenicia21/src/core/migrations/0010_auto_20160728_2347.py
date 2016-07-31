# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20160728_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faktura',
            name='sposob_platnosci',
            field=models.ForeignKey(null=True, blank=True, to='core.SposobPlatnosci'),
        ),
    ]
