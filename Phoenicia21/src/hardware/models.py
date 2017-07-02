from django.db import models
from core.models import Dokument, Jednostka

class Przedmiot(models.Model):
    # pojedynczy egzemplarz sprzetu
    
    opis                    = models.CharField(max_length=80)
    liczba                  = models.IntegerField()
    nr_ewidencyjny          = models.CharField(max_length=8) # format: hhjjnnnn; hh = id hufca, jj = id jednostki (z Phoenicii), nnnn = numer przedmiotu
    dokumenty_zakupu        = models.ManyToManyField(Dokument)
    opis_stanu              = models.CharField(max_length=200) 
    data_aktualizacji_stanu = models.DateField(auto_now_add=True)
    
    # definicje do typu sprzetu
    NAMIOT     = 'NM'
    PIONIERSKI = 'PN'
    KUCHENNY   = 'KN'
    SANITARNY  = 'SN'
    PROGRAMOWY = 'PG'
    INNY       = 'IN'
    
    TYP_SPRZETU_CHOICES = (
        (NAMIOT, 'Namiot'),
        (PIONIERSKI, 'Pionierski'),
        (KUCHENNY, 'Kuchenny'),
        (SANITARNY, 'Sanitarny'),
        (PROGRAMOWY, 'Programowy'),
        (INNY, 'Inny'),
    )
    
    typ = models.CharField(max_length=2,
                           choices=TYP_SPRZETU_CHOICES)
    
    # definicje opisu stanu sprzetu 
    NOWY         = 'NW5'
    BARDZO_DOBRY = 'BD4'
    DOBRY        = 'DB3'
    SREDNI       = 'SR2'
    ZLY          = 'ZL1'
    DO_WYCOFANIA = 'DW0'
    
    STAN_CHOICES = (
        (NOWY, 'Nowy'),
        (BARDZO_DOBRY, 'Bardzo dobry'),
        (DOBRY, 'Dobry'),
        (SREDNI, u'Średni'),
        (ZLY, u'Zły'),
        (DO_WYCOFANIA, 'Do wycofania'),
    )
    
    stan = models.CharField(max_length=3,
                            choices=STAN_CHOICES)
    
class Magazyn(models.Model):
    
    nazwa     = models.CharField(max_length=50)
    adres     = models.CharField(max_length=120)
    jednostki = models.ManyToManyField(Jednostka) 



