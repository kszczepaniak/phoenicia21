# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_uzytkownik_is_skarbnik'),
    ]

    operations = [
        migrations.AddField(
            model_name='bilansotwarcia',
            name='hufiec',
            field=models.ForeignKey(to='core.Hufiec', default=1),
            preserve_default=False,
        ),
    ]
