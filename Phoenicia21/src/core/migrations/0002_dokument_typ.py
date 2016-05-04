# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokument',
            name='typ',
            field=models.CharField(max_length=2, default='FV', choices=[('FV', 'Faktura VAT'), ('KP', 'KP'), ('DE', 'Delegacja'), ('BI', 'Bilety'), ('KW', 'KW'), ('NK', 'Nota księgowa'), ('PO', 'Polisa')]),
            preserve_default=False,
        ),
    ]
