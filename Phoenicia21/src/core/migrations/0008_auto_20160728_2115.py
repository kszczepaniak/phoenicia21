# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_uzytkownik_is_staff'),
    ]

    operations = [
        migrations.CreateModel(
            name='Faktura',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('numer', models.CharField(max_length=20)),
                ('data_wystawienia', models.DateField()),
                ('nabywca_nazwa', models.CharField(max_length=50)),
                ('nabywca_adres', models.CharField(max_length=80)),
                ('nabywca_nip', models.CharField(max_length=16)),
                ('kwota', models.DecimalField(max_digits=10, decimal_places=2)),
                ('stawka_vat', models.IntegerField()),
                ('tytul', models.CharField(max_length=200)),
                ('uwagi', models.CharField(max_length=200)),
                ('status', models.CharField(max_length=2, choices=[('ZG', 'Zgłoszona'), ('ZT', 'Zatwierdzona')])),
                ('jednostka', models.ForeignKey(to='core.Jednostka')),
            ],
        ),
        migrations.CreateModel(
            name='NumeracjaFaktur',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('rok', models.IntegerField()),
                ('kategoria', models.CharField(max_length=3, choices=[('HAL', 'HAL'), ('HAZ', 'HAZ'), ('ROK', 'Śródroczna')])),
            ],
        ),
        migrations.CreateModel(
            name='SposobPlatnosci',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('nazwa', models.CharField(max_length=50)),
                ('numer_konta', models.CharField(max_length=40)),
            ],
        ),
        migrations.AddField(
            model_name='faktura',
            name='sposob_platnosci',
            field=models.ForeignKey(to='core.SposobPlatnosci'),
        ),
        migrations.AddField(
            model_name='faktura',
            name='uzytkownik',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
