# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20170119_2332'),
    ]

    operations = [
        migrations.AddField(
            model_name='jednostka',
            name='hufiec',
            field=models.ForeignKey(to='core.Hufiec', default=1),
            preserve_default=False,
        ),
    ]
