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
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', blank=True, null=True)),
                ('login', models.CharField(max_length=40, unique=True)),
                ('imie', models.CharField(max_length=25)),
                ('nazwisko', models.CharField(max_length=45)),
                ('email', models.CharField(max_length=60)),
                ('is_active', models.BooleanField(default=False)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_skarbnik', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BilansOtwarcia',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('rok', models.IntegerField()),
                ('kwota', models.DecimalField(decimal_places=2, max_digits=12)),
            ],
        ),
        migrations.CreateModel(
            name='Dokument',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('data_dokumentu', models.DateField()),
                ('data_ksiegowania', models.DateField(auto_now_add=True)),
                ('typ', models.CharField(choices=[('FV', 'Faktura VAT'), ('KP', 'KP'), ('DE', 'Delegacja'), ('BI', 'Bilety'), ('KW', 'KW'), ('NK', 'Nota księgowa'), ('PO', 'Polisa')], max_length=2)),
                ('numer', models.CharField(max_length=50)),
                ('opis', models.CharField(max_length=70)),
                ('wplyw', models.DecimalField(decimal_places=2, max_digits=10)),
                ('wydatek', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('ZG', 'Zgłoszona'), ('ZT', 'Zatwierdzona')], max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Etykieta',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('nazwa', models.CharField(max_length=30)),
                ('systemowa', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Faktura',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('numer', models.CharField(max_length=20)),
                ('data_wystawienia', models.DateField(blank=True, null=True)),
                ('nabywca_nazwa', models.CharField(max_length=50)),
                ('nabywca_adres', models.CharField(max_length=80)),
                ('nabywca_nip', models.CharField(max_length=16)),
                ('kwota', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tytul', models.CharField(max_length=200)),
                ('uwagi', models.CharField(max_length=200)),
                ('status', models.CharField(choices=[('ZG', 'Zgłoszona'), ('ZT', 'Zatwierdzona')], max_length=2)),
                ('stawka_vat', models.CharField(choices=[('ZW', 'zw'), ('05', '5'), ('08', '8'), ('23', '23')], max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Hufiec',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('nazwa', models.CharField(max_length=40)),
                ('numer', models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='Jednostka',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('nazwa', models.CharField(max_length=50)),
                ('saldo', models.DecimalField(decimal_places=2, max_digits=10)),
                ('aktywna', models.BooleanField()),
                ('typ_jednostki', models.CharField(choices=[('PDS', 'Podstawowa'), ('NPD', 'Nie-podstawowa'), ('SZP', 'Szczep'), ('ZSH', 'Zespół Hufcowy'), ('TYM', 'Tymczasowa')], max_length=3, default='PDS')),
                ('hufiec', models.ForeignKey(to='core.Hufiec')),
            ],
        ),
        migrations.CreateModel(
            name='Kontrahent',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('nazwa', models.CharField(max_length=120)),
                ('adres_ulica', models.CharField(max_length=100)),
                ('adres_kod_miasto', models.CharField(max_length=50)),
                ('nip', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='NumeracjaFaktur',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('rok', models.IntegerField()),
                ('biezacy_numer', models.IntegerField()),
                ('kategoria', models.CharField(choices=[('HAL', 'HAL'), ('HAZ', 'HAZ'), ('ROK', 'Śródroczna')], max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='OperacjaSalda',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
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
        migrations.CreateModel(
            name='RaportKasowy',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('miesiac', models.IntegerField()),
                ('rok', models.IntegerField()),
                ('saldo_start', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('saldo_stop', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('numer_start', models.IntegerField(default=0)),
                ('numer_stop', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('UTW', 'Utworzony'), ('ZLO', 'Złożony'), ('ZAK', 'Zaakceptowany'), ('POP', 'Poprawiony')], max_length=3, default='UTW')),
                ('hufiec', models.ForeignKey(to='core.Hufiec')),
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
        migrations.CreateModel(
            name='Zaliczka',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('data_wystawienia', models.DateField(auto_now_add=True)),
                ('termin_rozliczenia', models.DateField()),
                ('tytul', models.CharField(max_length=80)),
                ('kwota', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('AKT', 'Aktywna'), ('ROZ', 'Rozliczona')], max_length=3)),
                ('hufiec', models.ForeignKey(to='core.Hufiec')),
                ('jednostka', models.ForeignKey(to='core.Jednostka')),
                ('pobierajacy', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('wystawiajacy', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='wystawiajacy')),
            ],
        ),
        migrations.AddField(
            model_name='faktura',
            name='jednostka',
            field=models.ForeignKey(to='core.Jednostka'),
        ),
        migrations.AddField(
            model_name='faktura',
            name='sposob_platnosci',
            field=models.ForeignKey(null=True, blank=True, to='core.SposobPlatnosci'),
        ),
        migrations.AddField(
            model_name='faktura',
            name='uzytkownik',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dokument',
            name='etykiety',
            field=models.ManyToManyField(to='core.Etykieta'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='hufiec',
            field=models.ForeignKey(to='core.Hufiec'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='jednostka',
            field=models.ForeignKey(to='core.Jednostka'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='kontrahent',
            field=models.ForeignKey(null=True, blank=True, to='core.Kontrahent'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='raport_kasowy',
            field=models.ForeignKey(null=True, blank=True, to='core.RaportKasowy'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='uzytkownik',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dokument',
            name='uzytkownik_zglaszajacy',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='zglaszajacy'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='zaliczka',
            field=models.ForeignKey(null=True, blank=True, to='core.Zaliczka'),
        ),
        migrations.AddField(
            model_name='bilansotwarcia',
            name='hufiec',
            field=models.ForeignKey(to='core.Hufiec'),
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
