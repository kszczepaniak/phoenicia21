# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20160730_2114'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokument',
            name='status',
            field=models.CharField(choices=[('ZG', 'Zgłoszona'), ('ZT', 'Zatwierdzona')], default='ZT', max_length=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dokument',
            name='uzytkownik_zglaszajacy',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, default=1, related_name='zglaszajacy'),
            preserve_default=False,
        ),
    ]
