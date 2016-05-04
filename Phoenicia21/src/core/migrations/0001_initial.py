# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Uzytkownik',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', blank=True, null=True)),
                ('login', models.CharField(max_length=40, unique=True)),
                ('imie', models.CharField(max_length=25)),
                ('nazwisko', models.CharField(max_length=45)),
                ('email', models.CharField(max_length=60)),
                ('is_active', models.BooleanField(default=True)),
                ('is_admin', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BilansOtwarcia',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('rok', models.IntegerField()),
                ('kwota', models.DecimalField(max_digits=12, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='Dokument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('data_dokumentu', models.DateField()),
                ('data_ksiegowania', models.DateField(auto_now_add=True)),
                ('numer', models.CharField(max_length=50)),
                ('opis', models.CharField(max_length=70)),
                ('wplyw', models.DecimalField(max_digits=10, decimal_places=2)),
                ('wydatek', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='Etykieta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('nazwa', models.CharField(max_length=30)),
                ('systemowa', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Hufiec',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('nazwa', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Jednostka',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('nazwa', models.CharField(max_length=50)),
                ('saldo', models.DecimalField(max_digits=10, decimal_places=2)),
                ('saldo_jeden_procent', models.DecimalField(max_digits=10, decimal_places=2)),
                ('aktywna', models.BooleanField()),
                ('typ_jednostki', models.CharField(choices=[('PDS', 'Podstawowa'), ('NPD', 'Nie-podstawowa'), ('SZP', 'Szczep'), ('ZSH', 'Zespół Hufcowy'), ('TYM', 'Tymczasowa')], default='PDS', max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='RaportKasowy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('miesiac', models.IntegerField()),
                ('rok', models.IntegerField()),
                ('saldo_start', models.DecimalField(max_digits=12, default=0.0, decimal_places=2)),
                ('saldo_stop', models.DecimalField(max_digits=12, default=0.0, decimal_places=2)),
                ('numer_start', models.IntegerField(default=0)),
                ('numer_stop', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('UTW', 'Utworzony'), ('ZLO', 'Złożony'), ('ZAK', 'Zaakceptowany'), ('POP', 'Poprawiony')], default='UTW', max_length=3)),
            ],
        ),
        migrations.AddField(
            model_name='dokument',
            name='etykiety',
            field=models.ManyToManyField(to='core.Etykieta'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='jednostka',
            field=models.ForeignKey(to='core.Jednostka'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='raport_kasowy',
            field=models.ForeignKey(blank=True, to='core.RaportKasowy', null=True),
        ),
        migrations.AddField(
            model_name='dokument',
            name='uzytkownik',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='uzytkownik',
            name='hufiec',
            field=models.ForeignKey(to='core.Hufiec'),
        ),
        migrations.AddField(
            model_name='uzytkownik',
            name='jednostka',
            field=models.ManyToManyField(to='core.Jednostka'),
        ),
    ]
