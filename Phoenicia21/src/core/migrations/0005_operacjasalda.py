# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20150524_0209'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperacjaSalda',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('data_operacji', models.DateField(auto_now_add=True)),
                ('opis', models.CharField(max_length=70)),
                ('kwota', models.DecimalField(decimal_places=2, max_digits=10)),
                ('typ_operacji', models.CharField(choices=[('TF', 'Transfer'), ('BK', 'Bankowa')], max_length=2)),
                ('etykiety', models.ManyToManyField(to='core.Etykieta')),
                ('jednostka_docelowa', models.ForeignKey(null=True, to='core.Jednostka', related_name='unit_target')),
                ('jednostka_zrodlowa', models.ForeignKey(null=True, to='core.Jednostka', related_name='unit_origin')),
                ('uzytkownik', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
