# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20161016_2034'),
    ]

    operations = [
        migrations.CreateModel(
            name='Zaliczka',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_wystawienia', models.DateField(auto_now_add=True)),
                ('termin_rozliczenia', models.DateField()),
                ('tytul', models.CharField(max_length=80)),
                ('kwota', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(max_length=3, choices=[('AKT', 'Aktywna'), ('ROZ', 'Rozliczona')])),
                ('jednostka', models.ForeignKey(to='core.Jednostka')),
                ('pobierajacy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='dokument',
            name='zaliczka',
            field=models.ForeignKey(to='core.Zaliczka', null=True, blank=True),
        ),
    ]
