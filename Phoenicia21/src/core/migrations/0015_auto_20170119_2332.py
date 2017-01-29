# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_zaliczka_wystawiajacy'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kontrahent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('nazwa', models.CharField(max_length=120)),
                ('adres_ulica', models.CharField(max_length=100)),
                ('adres_kod_miasto', models.CharField(max_length=50)),
                ('nip', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='dokument',
            name='hufiec',
            field=models.ForeignKey(default=1, to='core.Hufiec'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='hufiec',
            name='numer',
            field=models.CharField(max_length=5, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='raportkasowy',
            name='hufiec',
            field=models.ForeignKey(default=1, to='core.Hufiec'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dokument',
            name='kontrahent',
            field=models.ForeignKey(blank=True, null=True, to='core.Kontrahent'),
        ),
    ]
