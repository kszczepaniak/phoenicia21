# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_dokument_typ'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jednostka',
            name='saldo_jeden_procent',
        ),
    ]
