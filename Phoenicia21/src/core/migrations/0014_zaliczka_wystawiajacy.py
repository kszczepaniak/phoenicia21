# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20161106_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='zaliczka',
            name='wystawiajacy',
            field=models.ForeignKey(default=1, related_name='wystawiajacy', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
