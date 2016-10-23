from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class Etykieta(models.Model):
    nazwa     = models.CharField(max_length=30)
    systemowa = models.BooleanField()           # nie-usuwalna, wbudowana etykieta
    
    def __str__(self):
        return self.nazwa

class Dokument(models.Model):
    # pojedynczy dokument
    
    data_dokumentu    = models.DateField()                                   # data wystawienia dokumentu
    data_ksiegowania  = models.DateField(auto_now_add=True)                  # data wprowadzenia do systemu
    # definicje do typu dokumentu
    FAKTURA_VAT   = 'FV'
    KASA_PRZYJMIE = 'KP'
    DELEGACJA     = 'DE'
    BILETY        = 'BI'
    KASA_WYDA     = 'KW'
    NOTA_KSIEGOWA = 'NK'
    POLISA        = 'PO'
    TYP_DOKUMENTU_CHOICES = (
        (FAKTURA_VAT, 'Faktura VAT'),
        (KASA_PRZYJMIE, 'KP'),
        (DELEGACJA, 'Delegacja'),
        (BILETY, 'Bilety'),
        (KASA_WYDA, 'KW'),
        (NOTA_KSIEGOWA, u'Nota ksi\u0119gowa'),
        (POLISA, 'Polisa'),
    )
    
    typ = models.CharField(max_length=2,
                           choices=TYP_DOKUMENTU_CHOICES)
    
    dekret                 = models.ForeignKey('Dekret', blank=True, null=True)
    numer                  = models.CharField(max_length=50)
    opis                   = models.CharField(max_length=70)                      # krotki dowolny opis czego dotyczy dokument
    wplyw                  = models.DecimalField(max_digits=10, decimal_places=2)
    wydatek                = models.DecimalField(max_digits=10, decimal_places=2)
    etykiety               = models.ManyToManyField(Etykieta) 
    #zaliczka          = models.ForeignKey('Account', blank=True, null=True)
    uzytkownik             = models.ForeignKey('Uzytkownik')
    jednostka              = models.ForeignKey('Jednostka')
    #hufiec               = models.ForeignKey('Hufiec')
    raport_kasowy          = models.ForeignKey('RaportKasowy', blank=True, null=True)
    # pola potrzebne do zglaszania faktur
    uzytkownik_zglaszajacy = models.ForeignKey('Uzytkownik', related_name='zglaszajacy')
    ZGLOSZONA    = 'ZG'
    ZATWIERDZONA = 'ZT'
    STATUS_CHOICES = (
        (ZGLOSZONA, 'Zg\u0142oszona'),
        (ZATWIERDZONA, 'Zatwierdzona'),
    )
    status = models.CharField(max_length=2, choices=STATUS_CHOICES) 

class Dekret(models.Model):
    numer = models.CharField(max_length=16)
    opis  = models.CharField(max_length=64)
    
    def __str__(self):
        return self.numer

class OperacjaSalda(models.Model):
    # nie-gotowkowe operacje na saldach jednostek
    data_operacji      = models.DateField(auto_now_add=True)
    opis               = models.CharField(max_length=70)
    kwota              = models.DecimalField(max_digits=10, decimal_places=2)
    uzytkownik         = models.ForeignKey('Uzytkownik')
    jednostka_zrodlowa = models.ForeignKey('Jednostka', related_name='unit_origin', null=True)
    jednostka_docelowa = models.ForeignKey('Jednostka', related_name='unit_target', null=True)
    #hufiec         = models.ForeignKey('Hufiec')
    etykiety          = models.ManyToManyField(Etykieta)
    
    TRANSFER = 'TF'
    BANK     = 'BK'
    OPERATION_TYPE_CHOICES = (
        (TRANSFER, 'Transfer'),
        (BANK, 'Bankowa'),
    )
    typ_operacji = models.CharField(max_length=2,
                    choices=OPERATION_TYPE_CHOICES)

class Hufiec(models.Model):
    nazwa = models.CharField(max_length=40)

class Jednostka(models.Model):
    nazwa                = models.CharField(max_length=50)
    saldo                = models.DecimalField(max_digits=10, decimal_places=2)
    aktywna              = models.BooleanField()
    #hufiec              = models.ForeignKey('Hufiec')
    
    PODSTAWOWA     = 'PDS'
    NIEPODSTAWOWA  = 'NPD'
    SZCZEP         = 'SZP'
    ZESPOL_HUFCOWY = 'ZSH'
    TYMCZASOWA     = 'TYM'
    TYP_JEDNOSTKI_CHOICES = (
        (PODSTAWOWA, 'Podstawowa'),
        (NIEPODSTAWOWA, 'Nie-podstawowa'),
        (SZCZEP, 'Szczep'),
        (ZESPOL_HUFCOWY, u'Zesp\u00F3\u0142 Hufcowy'),
        (TYMCZASOWA, 'Tymczasowa'),
    )
    
    typ_jednostki = models.CharField(max_length=3,
                                 choices=TYP_JEDNOSTKI_CHOICES,
                                 default=PODSTAWOWA) 
    
    def __str__(self):
        return self.nazwa
    
class UserManager(BaseUserManager):
    def create_user(self, login, password, imie, nazwisko, email, hufiec, jednostka):
 
        user = self.model(login=login, imie=imie, nazwisko=nazwisko, email=email, hufiec=hufiec)
 
        user.set_password(password)
        user.save(using=self._db)
        
        jednostka = Jednostka.objects.get(id=jednostka)
        user.jednostka.add(jednostka)
        return user
 
    def create_superuser(self, login, password):
        user = self.create_user(login=login,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user
        
class Uzytkownik(AbstractBaseUser):
    login     = models.CharField(max_length=40, unique=True)
    imie      = models.CharField(max_length=25)
    nazwisko  = models.CharField(max_length=45)
    email     = models.CharField(max_length=60)
    jednostka = models.ManyToManyField(Jednostka)
    hufiec    = models.ForeignKey('Hufiec')
    
    # pola wymagane przez Django user model
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()

    USERNAME_FIELD = 'login'
    
    def __str__(self):
        return self.login
    
    def get_full_name(self):
        return self.login
    
    def get_short_name(self):
        return self.login
    
    def has_perm(self, perm, obj=None):
        # Handle whether the user has a specific permission?"
        return True
 
    def has_module_perms(self, app_label):
        # Handle whether the user has permissions to view the app `app_label`?"
        return True
    '''
    @property
    def is_staff(self):
        # Handle whether the user is a member of staff?"
        return self.is_staff
    '''

class RaportKasowy(models.Model):
    miesiac     = models.IntegerField()
    rok         = models.IntegerField()
    saldo_start = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    saldo_stop  = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    numer_start = models.IntegerField(default=0)
    numer_stop  = models.IntegerField(default=0)
    #hufiec        = models.ForeignKey('Hufiec')
    
    UTWORZONY     = 'UTW'
    ZLOZONY       = 'ZLO'
    ZAAKCEPTOWANY = 'ZAK'
    POPRAWIONY    = 'POP'
    STATUS_CHOICES = (
        (UTWORZONY, 'Utworzony'),
        (ZLOZONY, u'Z\u0142o\u017Cony'),
        (ZAAKCEPTOWANY, 'Zaakceptowany'),
        (POPRAWIONY, 'Poprawiony')
    )
    status = models.CharField(max_length=3,
                              choices=STATUS_CHOICES,
                              default=UTWORZONY)

class BilansOtwarcia(models.Model):
    rok    = models.IntegerField()
    kwota  = models.DecimalField(max_digits=12, decimal_places=2)
    #hufiec  = models.ForeignKey('Hufiec')

class SposobPlatnosci(models.Model):
    nazwa       = models.CharField(max_length=50)
    numer_konta = models.CharField(max_length=40)
    
    def __str__(self):
        return self.nazwa

class NumeracjaFaktur(models.Model):
    rok           = models.IntegerField()
    biezacy_numer = models.IntegerField()
    
    HAL = 'HAL'
    HAZ = 'HAZ'
    ROK = 'ROK'
    CATEGORY_TYPE_CHOICES = (
        (HAL, 'HAL'),
        (HAZ, 'HAZ'),
        (ROK, '\u015Ar\u00F3droczna'),
    )
    
    kategoria = models.CharField(max_length=3,
                    choices=CATEGORY_TYPE_CHOICES)
    
    def __str__(self):
        return self.kategoria + ' ' + str(self.rok)

class Faktura(models.Model):
    # faktury wystawiane przez hufiec (np. za obozy albo wynajem sprzetu)
    numer            = models.CharField(max_length=20)
    data_wystawienia = models.DateField(blank=True, null=True)
    nabywca_nazwa    = models.CharField(max_length=50)
    nabywca_adres    = models.CharField(max_length=80)
    nabywca_nip      = models.CharField(max_length=16)
    kwota            = models.DecimalField(max_digits=10, decimal_places=2) # kwota bez podatku
    tytul            = models.CharField(max_length=200)
    sposob_platnosci = models.ForeignKey('SposobPlatnosci', blank=True, null=True)
    uwagi            = models.CharField(max_length=200)
    uzytkownik       = models.ForeignKey('Uzytkownik')
    jednostka        = models.ForeignKey('Jednostka')
    #hufiec           = models.ForeignKey('Hufiec')
    
    ZGLOSZONA    = 'ZG'
    ZATWIERDZONA = 'ZT'
    STATUS_TYPE_CHOICES = (
        (ZGLOSZONA, 'Zg\u0142oszona'),
        (ZATWIERDZONA, 'Zatwierdzona'),
    )
    status = models.CharField(max_length=2,
                choices=STATUS_TYPE_CHOICES)
    
    ZWOLNIONE     = 'ZW'
    PIEC_PROCENT  = '05'
    OSIEM_PROCENT = '08'
    PODSTAWOWA    = '23'    
    VAT_TYPE_CHOICES = (
        (ZWOLNIONE, 'zw'),
        (PIEC_PROCENT, '5'),
        (OSIEM_PROCENT, '8'),
        (PODSTAWOWA, '23')
    )
    stawka_vat = models.CharField(max_length=2,
                    choices=VAT_TYPE_CHOICES)
    
    