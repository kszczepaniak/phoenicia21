from django.db import models
from core.models import Jednostka, Uzytkownik

class UczestnikBiwaku(models.Model):
    
    # przy dodawaniu nalezy weryfikowac format ewidencja_id
    # dodajac sprawdza sie tez czy dany ewidencja_id juz jest w bazie i jezeli tak to nie dodaje ponownie
    
    imie         = models.CharField(max_length=25)
    nazwisko     = models.CharField(max_length=45)
    ewidencja_id = models.CharField(max_length=11)  

class Biwak(models.Model):
    
    organizator            = models.ForeignKey(Jednostka)
    termin_start           = models.DateField()
    termin_stop            = models.DateField()
    miejsce                = models.CharField(max_length=120)
    uczestnicy_miasto      = models.IntegerField()
    uczestnicy_wies        = models.IntegerField()
    sposob_wyzywienia      = models.CharField(max_length=120)
    warunki_zakwaterowania = models.CharField(max_length=120)
    druzynowy              = models.ForeignKey(Uzytkownik)
    opiekunowie            = models.CharField(max_length=200) # oddzieleni ',', przy dodawaniu robic strip() aby sie nie psulo
    program_biwaku         = models.FileField(upload_to='\office\media\programy_biwaku')
    lista_uczestnikow      = models.ManyToManyField(UczestnikBiwaku)
    
    # definicje zapewnienia srodkow finansowych
    UCZESTNICY = 'UC'
    DRUZYNA    = 'DR'
    MIESZANE   = 'MS'
    
    SRODKI_CHOICES = (
        (UCZESTNICY, u'Wpłaty uczestników'),
        (DRUZYNA, u'Środki drużyny'),
        (MIESZANE, u'Wpłaty uczestników i środki drużyny'),
    )
    
    zapewnienie_srodkow = models.CharField(max_length=2,
                                           choices=SRODKI_CHOICES)

    
