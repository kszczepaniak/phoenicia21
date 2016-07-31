# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20160728_2347'),
    ]

    operations = [
        migrations.AddField(
            model_name='numeracjafaktur',
            name='biezacy_numer',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='faktura',
            name='stawka_vat',
            field=models.CharField(max_length=2, choices=[('ZW', 'zw'), ('05', '5'), ('08', '8'), ('23', '23')]),
        ),
    ]
