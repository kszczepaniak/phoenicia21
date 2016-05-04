# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_jednostka_saldo_jeden_procent'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dekret',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('numer', models.CharField(max_length=16)),
                ('opis', models.CharField(max_length=64)),
            ],
        ),
        migrations.AddField(
            model_name='dokument',
            name='dekret',
            field=models.ForeignKey(to='core.Dekret', null=True, blank=True),
        ),
    ]
