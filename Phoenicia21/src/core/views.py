from datetime import date
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from core.models import Dokument, Uzytkownik, Jednostka, Hufiec, RaportKasowy, BilansOtwarcia, Etykieta, Dekret, OperacjaSalda, Faktura, NumeracjaFaktur, SposobPlatnosci
import re, decimal, datetime, random, string
# reportlab imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics, ttfonts
from django.http import HttpResponse
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config
from django.template.context_processors import request

# email uzywany przez system do rozsylania wiadomosci
EMAIL_SYSTEMU = 'kszczepaniak@gmx.com'
# na ten email przychodza informaje z systemu takie jak o rejestracji nowego uzytkownika
EMAIL_ADMINA  = 'kszczepaniak@gmx.com'

MIESIACE = ((1, u'Stycze\u0144'), (2, 'Luty'), (3, 'Marzec'),
            (4, u'Kwiecie\u0144'), (5, 'Maj'), (6, 'Czerwiec'),
            (7, 'Lipiec'), (8, u'Sierpie\u0144'), (9, u'Wrzesie\u0144'),
            (10, u'Pa\u017Adziernik'), (11, 'Listopad'), (12, u'Grudzie\u0144'))

def main(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    
    context = {}
    return render(request, 'core/main.html', context)

def docs_add(request):
    '''
    dodawanie pojedynczego dokumentu do bazy
    '''
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        return redirect('access_denied')    
    
    def validate_data(request):        
        # walidacja danych, w przypadku znalezienia bledu
        # jest on dodawany do listy error_log, ktora jest
        # potem przekazywana do html w celu wyswietlenia komunikatu bledu
        error_log = []
        
        if not (re.search('^\d{4}-[0-1]\d-[0-3]\d$', request.POST['data_dokumentu'])): error_log.append('data_dokumentu')  
        if not request.POST['numer']: error_log.append('numer')
        if not request.POST['opis']: error_log.append('opis')
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['wplyw'])): error_log.append('kwota')
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['wydatek'])): error_log.append('kwota')
        # jezeli format kwoty sie zgadza sprawdza czy wplyw XOR wydatek
        if 'kwota' not in error_log:
            if (request.POST['wplyw'] == '' and request.POST['wydatek'] == ''): error_log.append('kwota_brak')
            elif (request.POST['wplyw'] == '' or request.POST['wydatek'] == ''): pass
            elif (float(request.POST['wplyw'].replace(',', '.')) and float(request.POST['wydatek'].replace(',', '.'))): error_log.append('kwota_oba')    
        
        return error_log 
    
    def add_document(request):
        
        def change_balance(jednostka, wplyw, wydatek):
            # zmiana salda
            
            jednostka.saldo += decimal.Decimal(wplyw)
            jednostka.saldo -= decimal.Decimal(wydatek)
            jednostka.save()
        
        jednostka = Jednostka.objects.get(id=request.POST['jednostka'])
        
        # ustaw wplyw/wydatek na 0.0 jezeli pozostal nieywpelniony
        wplyw   = 0.0 if request.POST['wplyw'] == '' else request.POST['wplyw'].replace(',', '.')
        wydatek = 0.0 if request.POST['wydatek'] == '' else request.POST['wydatek'].replace(',', '.')
        
        dokument = Dokument(data_dokumentu=request.POST['data_dokumentu'], typ=request.POST['typ'], numer=request.POST['numer'], opis=request.POST['opis'], wplyw=wplyw, 
                            wydatek=wydatek, jednostka=jednostka, uzytkownik=request.user, uzytkownik_zglaszajacy=request.user, status='ZT')        
        dokument.save()
        
        # dodwanie etykiet
        etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety') ]
        dokument.etykiety.add(*etykiety)

        # zwiekszenie/zmniejszenie salda jednostki o kwote dokumentu
        change_balance(jednostka, wplyw, wydatek)

    if request.method == 'POST':
        error_log = validate_data(request)
        if not error_log:
            add_document(request)
    else:
        error_log = []
           
    # dane potrzebne do formularza dodawania
    jednostki = Jednostka.objects.all().order_by('nazwa')
    etykiety  = Etykieta.objects.all()  
    
    context = {'error_log':error_log, 'jednostki':jednostki, 'etykiety':etykiety, 'typy_dokumentow':Dokument.TYP_DOKUMENTU_CHOICES}
    return render(request, 'core/docs_add.html', context)

def docs_search(request):
    '''
    wyszukiwanie dokumentow w bazie, na znalezionych dokumentach mozna wykonac operacje edycji lub usuwania
    '''
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        # ograniczenie wyboru jednostek
        jednostki = request.user.jednostka.all().order_by('nazwa')
    else:
        jednostki = Jednostka.objects.all().order_by('nazwa')
    
    today    = date.today()
    etykiety = Etykieta.objects.all()
    context  = {'today': today, 'jednostki': jednostki, 'etykiety':etykiety, 'typy_dokumentow':Dokument.TYP_DOKUMENTU_CHOICES}

    def validate_data(request, dok, dok_id, error_log):
        # weryfikacja danych przy edycji dokumentow
        
        kwota = False
        
        if not (re.search('^\d{4}-[0-1]\d-[0-3]\d$', request.POST.getlist('data_dokumentu')[dok])): error_log.add(dok_id)
          
        if not request.POST.getlist('numer')[dok]: error_log.add(dok_id)
        if not request.POST.getlist('opis')[dok]: error_log.add(dok_id)
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST.getlist('wplyw')[dok])): 
            error_log.add(dok_id)
            kwota = True
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST.getlist('wydatek')[dok])): 
            error_log.add(dok_id)
            kwota = True
        
        if not kwota:
            if (request.POST.getlist('wplyw')[dok] == '' and request.POST.getlist('wydatek')[dok] == ''):
                error_log.add(dok_id)
            elif (request.POST.getlist('wplyw')[dok] == '' or request.POST.getlist('wydatek')[dok] == ''): pass
            elif (float(request.POST.getlist('wplyw')[dok].replace(',', '.')) and float(request.POST.getlist('wydatek')[dok].replace(',', '.'))):
                error_log.add(dok_id)
        
    def validate_data_search(request):
        error_log = []
        # sprawdzanie poprawnosci formatu daty
        for date in ['data_dokumentu_start', 'data_dokumentu_stop', 'data_ksiegowania_start', 'data_ksiegowania_stop']:
            if not (re.search('^\d{4}-[0-1]\d-[0-3]\d$|^$', request.POST[date])): error_log.append('data')
        
        return error_log

    def search_data(request):
        kwargs    = {}
        from django.db.models import Q
        
        # wybieranie tylko faktur zatwierdzonych do wykonywania operacji na nich
        kwargs['status'] = 'ZT'
                
        if request.POST['jednostka'] != '0':
            kwargs['jednostka'] = int(request.POST['jednostka'])
            
        if request.POST['opis'] != '':    
            kwargs['opis__contains'] = request.POST['opis']
            
        if request.POST['typ'] != '0':    
            kwargs['typ'] = request.POST['typ']
            
        if request.POST['numer'] != '':    
            kwargs['numer__contains'] = request.POST['numer']
        if request.POST.getlist('etykieta'):
            kwargs['etykiety__in'] = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykieta') ]
        if request.POST['data_dokumentu_start'] != '':
            date_raw = request.POST['data_dokumentu_start'].split('-')
            start_date = datetime.date(int(date_raw[0]), int(date_raw[1]), int(date_raw[2]))
            date_raw = request.POST['data_dokumentu_stop'].split('-')
            end_date = datetime.date(int(date_raw[0]), int(date_raw[1]), int(date_raw[2]))
            kwargs['data_dokumentu__range'] = (start_date, end_date)
        if request.POST['data_ksiegowania_start'] != '':
            date_raw = request.POST['data_ksiegowania_start'].split('-')
            start_date = datetime.date(int(date_raw[0]), int(date_raw[1]), int(date_raw[2]))
            date_raw = request.POST['data_ksiegowania_stop'].split('-')
            end_date = datetime.date(int(date_raw[0]), int(date_raw[1]), int(date_raw[2]))
            kwargs['data_ksiegowania__range'] = (start_date, end_date)
        if request.POST['kwota_start'] == '':
            kwota_start = decimal.Decimal(0.01)
        elif float(request.POST['kwota_start']) == 0.0:
            kwota_start = decimal.Decimal(0.01)
        else:
            kwota_start = decimal.Decimal(request.POST['kwota_start'])
        if request.POST['kwota_stop'] == '':
            kwota_stop = decimal.Decimal(1000000.0)
        else:
            kwota_stop = decimal.Decimal((request.POST['kwota_stop']))
        args = ( Q( wplyw__range = (kwota_start, kwota_stop) ) | Q( wydatek__range = (kwota_start, kwota_stop) ), )    
                
        dokumenty = Dokument.objects.filter(*args, **kwargs)   
        return dokumenty

    def change_document(request, dok):
        ###!!! jak beda tagi to trzeba bedzie cos z tym zrobic
        #one_percent = True if 'one_percent' + str(doc_id) in request.POST else False
        #enterprise = True if 'enterprise' + str(doc_id) in request.POST else False
        
        ###!!! do stuff with this    
        # find objects that are pointed in POST data, assign them
        #doc_type = DocType.objects.get(id=request.POST.getlist('type')[doc])
        #unit     = Unit.objects.get(id=request.POST.getlist('unit')[doc])
        def change_balance(request, dokument, new_unit, dok):
            # zmiana salda jezeli nastapila zmiana kwoty
            
            # jednostka sie nie zmienila
            old_unit = dokument.jednostka
            
            if old_unit == new_unit:
                wplyw_difference   = dokument.wplyw - decimal.Decimal(request.POST.getlist('wplyw')[dok].replace(',', '.'))
                wydatek_difference = dokument.wydatek - decimal.Decimal(request.POST.getlist('wydatek')[dok].replace(',', '.')) 
                new_unit.saldo -= wplyw_difference
                new_unit.saldo += wydatek_difference

            # jednostka sie zmienila       
            else:
                old_unit.saldo -= dokument.wplyw
                old_unit.saldo += dokument.wydatek
                new_unit.saldo += decimal.Decimal(request.POST.getlist('wplyw')[dok].replace(',', '.'))
                new_unit.saldo -= decimal.Decimal(request.POST.getlist('wydatek')[dok].replace(',', '.'))
                old_unit.save()
            new_unit.save()        
        
        # znajdz edytowany dokument w bazie
        dokument = Dokument.objects.get(id=dok_id)
        
        new_unit = Jednostka.objects.get(id=request.POST.getlist('jednostka')[dok])
        
        change_balance(request, dokument, new_unit, dok)
        dokument.data_dokumentu = request.POST.getlist('data_dokumentu')[dok]
        dokument.typ            = request.POST.getlist('typ')[dok]
        dokument.numer          = request.POST.getlist('numer')[dok]
        dokument.opis           = request.POST.getlist('opis')[dok]
        dokument.wplyw          = request.POST.getlist('wplyw')[dok].replace(',', '.')
        dokument.wydatek        = request.POST.getlist('wydatek')[dok].replace(',', '.')
        dokument.jednostka      = new_unit
        # usun wszystkie etykiety i dodaj wybrane w edycji (czyli pozostawia niezmienione w efekcie)
        dokument.etykiety.clear()
        etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety' + str(dokument.id)) ]
        dokument.etykiety.add(*etykiety)        
        dokument.save()
    
    # zostaje wykonane wyszukiwanie dokumentow i zwrocone wyniki
    if 'search' in request.POST:
        error_log = validate_data_search(request)
        if not error_log:
            context['dokumenty'] = search_data(request)
        else:
            context['error_log'] = error_log
    
    # wyswietla dokumenty do edycji        
    elif 'edit' in request.POST:
        context['edytowane_dokumenty'] = []
        for dok_id in request.POST.getlist('pick'):
            context['edytowane_dokumenty'].append(Dokument.objects.get(id=dok_id))
   
    # wprowadzenie zmian w dokumentach
    elif 'change' in request.POST:
        context['edytowane_dokumenty'] = []
        error_log = set()
        for dok in range(len(request.POST.getlist('pick'))):
            dok_id = request.POST.getlist('pick')[dok]
            validate_data(request, dok, dok_id, error_log)
            if dok_id not in error_log:
                change_document(request, dok)    
        for dok_id in error_log:
            context['edytowane_dokumenty'].append(Dokument.objects.get(id=dok_id))
        context['error_log'] = error_log
        context['default'] = 'search'
        
    # wyswietla liste wybranych do usuniecia dokumentow i prosi o potwierdzenie
    elif 'delete' in request.POST:
        context['usuwane_dokumenty'] = []
        for dok_id in request.POST.getlist('pick'):
            context['usuwane_dokumenty'].append(Dokument.objects.get(id=dok_id))
        
    # usuwanie wybranych dokumentow
    elif 'del_confirm' in request.POST:
        for dok_id in request.POST.getlist('pick'):
            del_dok = Dokument.objects.get(id=dok_id)
            
            # zmien saldo jednostki powiazanej z dokumentem
            del_dok.jednostka.saldo -= del_dok.wplyw
            del_dok.jednostka.saldo += del_dok.wydatek
            del_dok.jednostka.save()
               
            del_dok.delete()
        context['default'] = 'search'
    
    # wyswietla liste raportow i pozwala dodac dokumenty do wybranego
    elif 'add_to_report' in request.POST:    
        dokumenty = [ Dokument.objects.get(id=doc_id) for doc_id in request.POST.getlist('pick') ]
        raporty = RaportKasowy.objects.order_by('rok', 'miesiac')
        
        context['raporty'] = raporty 
        context['dokumenty_do_dodania'] = dokumenty
    
    # wykonanie operacji dodania dokumentow do raportu
    elif 'add_to_report_confirm' in request.POST:
        raport = RaportKasowy.objects.get(id=int(request.POST['raport']))
        
        for dok_id in request.POST.getlist('pick'):    
            dok = Dokument.objects.get(id=dok_id)
            dok.raport_kasowy = raport
            dok.save()
            
    else:
        context['default'] = 'search'

    return render(request, 'core/docs_search.html', context)

def docs_confirm(request):
    
    if not request.user.is_authenticated():
        return redirect('auth_login')
    
    def validate_data(request, dok, dok_id, error_log):
        # weryfikacja danych przy edycji dokumentow
        
        kwota = False
        
        if not (re.search('^\d{4}-[0-1]\d-[0-3]\d$', request.POST.getlist('data_dokumentu')[dok])): error_log.add(dok_id)
          
        if not request.POST.getlist('numer')[dok]: error_log.add(dok_id)
        if not request.POST.getlist('opis')[dok]: error_log.add(dok_id)
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST.getlist('wplyw')[dok])): 
            error_log.add(dok_id)
            kwota = True
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST.getlist('wydatek')[dok])): 
            error_log.add(dok_id)
            kwota = True
        
        if not kwota:
            if (request.POST.getlist('wplyw')[dok] == '' and request.POST.getlist('wydatek')[dok] == ''):
                error_log.add(dok_id)
            elif (request.POST.getlist('wplyw')[dok] == '' or request.POST.getlist('wydatek')[dok] == ''): pass
            elif (float(request.POST.getlist('wplyw')[dok].replace(',', '.')) and float(request.POST.getlist('wydatek')[dok].replace(',', '.'))):
                error_log.add(dok_id)    
    
    def change_document_confirm(request, dok): 
        ''' ta wersja funkcji nie zmienia salda - zgloszona faktura nie wplywa na saldo poki nie zostanie zatwierdzona '''    
        
        # znajdz edytowany dokument w bazie
        dokument = Dokument.objects.get(id=dok_id)
        new_unit = Jednostka.objects.get(id=request.POST.getlist('jednostka')[dok])
        
        dokument.data_dokumentu = request.POST.getlist('data_dokumentu')[dok]
        dokument.typ            = request.POST.getlist('typ')[dok]
        dokument.numer          = request.POST.getlist('numer')[dok]
        dokument.opis           = request.POST.getlist('opis')[dok]
        dokument.wplyw          = request.POST.getlist('wplyw')[dok].replace(',', '.')
        dokument.wydatek        = request.POST.getlist('wydatek')[dok].replace(',', '.')
        dokument.jednostka      = new_unit
        # usun wszystkie etykiety i dodaj wybrane w edycji (czyli pozostawia niezmienione w efekcie)
        dokument.etykiety.clear()
        etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety' + str(dokument.id)) ]
        dokument.etykiety.add(*etykiety)        
        dokument.save()  
        
    def change_balance(jednostka, wplyw, wydatek):
        # zmiana salda
        
        jednostka.saldo += decimal.Decimal(wplyw)
        jednostka.saldo -= decimal.Decimal(wydatek)
        jednostka.save()
    
    if (request.user.is_staff or request.user.is_admin):  
        jednostki       = Jednostka.objects.all().order_by('nazwa')
        typy_dokumentow = Dokument.TYP_DOKUMENTU_CHOICES
    else:
        jednostki = request.user.jednostka.all().order_by('nazwa')
        typy_dokumentow = (('FV', 'Faktura VAT'),)
    etykiety = Etykieta.objects.all()
    context  = {'jednostki': jednostki, 'etykiety':etykiety, 'typy_dokumentow':typy_dokumentow}
    
    # wyswietla dokumenty do edycji        
    if 'edit' in request.POST:
        context['edytowane_dokumenty'] = []
        for dok_id in request.POST.getlist('pick'):
            context['edytowane_dokumenty'].append(Dokument.objects.get(id=dok_id))
   
    # wprowadzenie zmian w dokumentach
    elif 'change' in request.POST:
        context['edytowane_dokumenty'] = []
        error_log = set()
        for dok in range(len(request.POST.getlist('pick'))):
            dok_id = request.POST.getlist('pick')[dok]
            validate_data(request, dok, dok_id, error_log)
            if dok_id not in error_log:
                change_document_confirm(request, dok)    
        for dok_id in error_log:
            context['edytowane_dokumenty'].append(Dokument.objects.get(id=dok_id))
        context['error_log'] = error_log
        context['default'] = 'search'
        
    # wyswietla liste wybranych do odrzucenia dokumentow i prosi o potwierdzenie
    elif 'reject' in request.POST:
        context['usuwane_dokumenty'] = []
        for dok_id in request.POST.getlist('pick'):
            context['usuwane_dokumenty'].append(Dokument.objects.get(id=dok_id))
        
    # usuwanie wybranych dokumentow
    elif 'reject_confirm' in request.POST:
        for dok_id in request.POST.getlist('pick'):
            del_dok = Dokument.objects.get(id=dok_id)   
            del_dok.delete()     
        context['default'] = 'search'
    
    elif 'confirm' in request.POST:
        for dok_id in request.POST.getlist('pick'):
            conf_dok = Dokument.objects.get(id=dok_id)
            conf_dok.uzytkownik = request.user
            conf_dok.status = 'ZT'
            conf_dok.data_ksiegowania = datetime.datetime.now()
            conf_dok.save()   
            change_balance(conf_dok.jednostka, conf_dok.wplyw, conf_dok.wydatek)
    
    else:
        if (request.user.is_staff or request.user.is_admin):
            dokumenty = Dokument.objects.filter(status='ZG')
        else:
            jednostki = request.user.jednostka.all().order_by('nazwa')
            dokumenty = Dokument.objects.filter(status='ZG', jednostka__in=jednostki)
        context['dokumenty'] = dokumenty
        
    return render(request, 'core/docs_confirm.html', context)

def register_docs(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    
    def validate_data(request):        
        # walidacja danych, w przypadku znalezienia bledu
        # jest on dodawany do listy error_log, ktora jest
        # potem przekazywana do html w celu wyswietlenia komunikatu bledu
        error_log = []
        
        if not (re.search('^\d{4}-[0-1]\d-[0-3]\d$', request.POST['data_dokumentu'])): error_log.append('data_dokumentu')  
        if not request.POST['numer']: error_log.append('numer')
        if not request.POST['opis']: error_log.append('opis')
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['wplyw'])): error_log.append('kwota')
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['wydatek'])): error_log.append('kwota')
        # jezeli format kwoty sie zgadza sprawdza czy wplyw XOR wydatek
        if 'kwota' not in error_log:
            if (request.POST['wplyw'] == '' and request.POST['wydatek'] == ''): error_log.append('kwota_brak')
            elif (request.POST['wplyw'] == '' or request.POST['wydatek'] == ''): pass
            elif (float(request.POST['wplyw'].replace(',', '.')) and float(request.POST['wydatek'].replace(',', '.'))): error_log.append('kwota_oba')    
        
        return error_log 
    
    def register_document(request):
               
        jednostka = Jednostka.objects.get(id=request.POST['jednostka'])
        
        # ustaw wplyw/wydatek na 0.0 jezeli pozostal nieywpelniony
        wplyw   = 0.0 if request.POST['wplyw'] == '' else request.POST['wplyw'].replace(',', '.')
        wydatek = 0.0 if request.POST['wydatek'] == '' else request.POST['wydatek'].replace(',', '.')
        
        dokument = Dokument(data_dokumentu=request.POST['data_dokumentu'], typ='FV', numer=request.POST['numer'], opis=request.POST['opis'], wplyw=wplyw, 
                            wydatek=wydatek, jednostka=jednostka, uzytkownik=request.user, uzytkownik_zglaszajacy=request.user, status='ZG')        
        dokument.save()
        
        # dodwanie etykiet
        etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety') ]
        dokument.etykiety.add(*etykiety)
         
    if request.method == 'POST':
        error_log = validate_data(request)
        if not error_log:
            register_document(request)
    else:
        error_log = []
    
    etykiety  = Etykieta.objects.all()
    jednostki = request.user.jednostka.all().order_by('nazwa')
    context   = {'error_log':error_log, 'jednostki': jednostki, 'etykiety':etykiety}
    
    return render(request, 'core/register_docs.html', context)

def auth_login(request):
    
    def validate_data(request):
        error_log = []
        # zgodnosc hasla
        if request.POST['haslo'] != request.POST['powtorz_haslo']: error_log.append('haslo')
        # brak jednostki
        if request.POST['jednostka'] == '0': error_log.append('jednostka')
        # brak danych: imie,nazwisko, email, nazwa
        if request.POST['imie'] == '' or request.POST['nazwisko'] == '' or request.POST['email'] == '' or request.POST['nazwa'] == '': error_log.append('dane_osobowe')
        # nazwa uzytkownika juz zajeta
        if len(Uzytkownik.objects.filter(login=request.POST['nazwa'])) > 0: error_log.append('nazwa_istnieje')
        # sprawdz czy email nie jest juz uzywany przez innego uzytkownika
        if len(Uzytkownik.objects.filter(email=request.POST['email'])) > 0: error_log.append('email_istnieje')
        return error_log
    
    context = {}
    if 'create_user' in request.POST:
        context['create'] = 1
        context['jednostki'] = Jednostka.objects.filter(typ_jednostki__in=['PDS', 'SZP', 'ZSH', 'NPD']).order_by('nazwa')
    if 'create_new' in request.POST:
        
        error_log = validate_data(request)
        
        ###!!! inicjaliacja hufca, zmienic do produkcji
        if len(Hufiec.objects.all()) == 0:
            hufiec = Hufiec(nazwa='SuperHufiec')
            hufiec.save()
        else:
            hufiec = Hufiec.objects.get(id=1)
        
        if error_log: 
            context['error_log'] = error_log
            context['create'] = 1
            context['jednostki'] = Jednostka.objects.filter(typ_jednostki__in=['PDS', 'SZP', 'ZSH', 'NPD']).order_by('nazwa')
        else:
            user = Uzytkownik.objects.create_user(request.POST['nazwa'], request.POST['haslo'], imie=request.POST['imie'], 
                                            nazwisko=request.POST['nazwisko'], email=request.POST['email'], hufiec=hufiec,
                                            jednostka=request.POST['jednostka'])
            # wyslij maila z powiadomieniem o nowym uzytkowniku
            temat = '[ZFH] Utworzono nowego użytkownika'
            tresc = 'To jest automatyczna wiadomość.\nNa stronie Zespołu Finansowego zarejestrował się nowy użytkownik.\nZaloguj się i aktywuj jego konto.'
            tresc += '\n\n---\n System Księgowy "Phoenicia"'
            # ponizsza funkcjonalnosc wymaga skonfigurowanego maila, jezeli testujesz rejestracje uzytkownikow bez skonfigurowanego maila zakomentuj
            # ! WAZNE: odkomentuj jak skonczysz testowac, inaczej do produkcji moze pojsc wersja bez tej funkcjonalnosci
            send_mail(temat, tresc, EMAIL_SYSTEMU, [EMAIL_ADMINA], fail_silently=False)
            context['user_create_success'] = 1
    
    if 'login' in request.POST:
        username = request.POST['nazwa']
        password = request.POST['haslo']
        user = authenticate(login=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('main')
            else:
                context['nieaktywny'] = 'nieaktywny'
        else:
            context['niepowodzenie'] = 'niepowodzenie'
    
    return render(request, 'core/auth_login.html', context)

def auth_logout(request):
    logout(request)
    
    context = {}
    return render(request, 'core/auth_login.html', context)

def profile(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    
    uzytkownik = request.user
    context = {'uzytkownik':uzytkownik}
    
    if 'zmien' in request.POST:
        error_log = []
        if not uzytkownik.check_password(request.POST['stare_haslo']):
            error_log.append('zle_stare_haslo')
        elif not request.POST['nowe_haslo'] == request.POST['nowe_haslo_powtorz']:
            error_log.append('niezgodne_nowe_haslo')
        elif len(request.POST['nowe_haslo']) == 0:
            error_log.append('krotkie_haslo')
        else:
            uzytkownik.set_password(request.POST['nowe_haslo'])
            uzytkownik.save()
            context['sukces'] = 'sukces'
        context['error_log'] = error_log
    
    return render(request, 'core/profile.html', context)

def restore_password(request):
    context = {}
    if 'reset' in request.POST:
        error_log = []
        email = request.POST['email']
        # sprawdz czy podany email znajduje sie w bazie uzytkownikow
        if len(Uzytkownik.objects.filter(email=email)) > 0:
            # wygeneruj losowe haslo
            new_password = ''.join([random.choice(string.digits + string.ascii_letters + '!@#$%^&*()') for _ in range(random.randint(6, 8))])
            
            # zmien haslo uzytkownika w bazie
            uzytkownik = Uzytkownik.objects.get(email=email)
            uzytkownik.set_password(new_password)
            uzytkownik.save()
            
            # wyslij maila z nowym haslem
            temat = '[ZFH] Zmiana hasła do konta'
            tresc = 'To jest automatyczna wiadomość.\nNa stronie Zespołu Finansowego wykonano żądanie zmiany hasła dla Twojego konta.\nTwoje tymczasowe hasło: ' + new_password
            tresc += '\nPo zalogowaniu się zmień hasło w zakładce "Profil".\n\n---\n System Księgowy "Phoenicia"'
            send_mail(temat, tresc, EMAIL_SYSTEMU, [email], fail_silently=False)
             
            context['wyslano'] = 'wyslano'
        else:
            error_log.append('nieznany_email')
            context['error_log'] = error_log

    return render(request, 'core/restore_password.html', context)

def access_denied(request):
    context = {}
    return render(request, 'core/access_denied.html', context)

def admin_units(request):
    '''
    administracja jednostkami: dodawanie, edycja i usuwanie
    '''
    ###!!! zaimplementowac edycje i usuwanie (na podstawie dokumentow)
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not request.user.is_admin:
        return redirect('access_denied')

    jednostki = Jednostka.objects.all()
    context = {'jednostki': jednostki, 'typy_jednostek': Jednostka.TYP_JEDNOSTKI_CHOICES}
    
    if 'add' in request.POST:
        aktywna = True if 'aktywna' in request.POST else False
                
        jednostka = Jednostka(nazwa=request.POST['nazwa'], saldo=request.POST['saldo'],
                    typ_jednostki=request.POST['typ_jednostki'], aktywna=aktywna) 
        jednostka.save()
        
    # wyswietla jednostki do edycji        
    elif 'edit' in request.POST:
        context['edytowane_jednostki'] = []
        for dok_id in request.POST.getlist('pick'):
            context['edytowane_jednostki'].append(Jednostka.objects.get(id=dok_id))
            
    # wprowadzenie zmian w jednostkach
    elif 'change' in request.POST:
        for jed in range(len(request.POST.getlist('pick'))):
            jed_id = request.POST.getlist('pick')[jed]
            
            # znajdz jednostke i wykonaj zmiany
            jednostka = Jednostka.objects.get(id=jed_id)
            jednostka.nazwa         = request.POST.getlist('nazwa')[jed]
            jednostka.typ_jednostki = request.POST.getlist('typ_jednostki')[jed]
            jednostka.aktywna       = True if request.POST.getlist('aktywna')[jed] == "1" else False
            jednostka.save()

    return render(request, 'core/admin_units.html', context)

def admin_users(request):
    '''
    administracja uzytkownikow: dodawanie, edycja i usuwanie
    '''
    ###!!! zaimplementowac edycje i usuwanie (na podstawie dokumentow)
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not request.user.is_admin:
        return redirect('access_denied')

    uzytkownicy = Uzytkownik.objects.all()
    context = {'uzytkownicy': uzytkownicy}
        
    # wyswietla uzytkownikow do edycji        
    if 'edit' in request.POST:
        context['edytowani_uzytkownicy'] = []
        for uzyt_id in request.POST.getlist('pick'):
            context['edytowani_uzytkownicy'].append(Uzytkownik.objects.get(id=uzyt_id))
            
    # wprowadzenie zmian w uzytkownikach
    elif 'change' in request.POST:
        for uzyt in range(len(request.POST.getlist('pick'))):
            uzyt_id = request.POST.getlist('pick')[uzyt]
            
            # znajdz uzytkonika i wykonaj zmiany
            uzytkownik = Uzytkownik.objects.get(id=uzyt_id)
            uzytkownik.is_admin  = True if request.POST.getlist('admin')[uzyt] == "1" else False
            uzytkownik.is_staff  = True if request.POST.getlist('staff')[uzyt] == "1" else False
            uzytkownik.is_active = True if request.POST.getlist('aktywny')[uzyt] == "1" else False
            uzytkownik.save()
    
    elif 'add_units' in request.POST:
        # wczytaj uzytkownikow do ktrych beda dodane jednostki
        context['uzytkownicy_do_jednostek'] = []
        for uzyt_id in request.POST.getlist('pick'):
            context['uzytkownicy_do_jednostek'].append(Uzytkownik.objects.get(id=uzyt_id))
        # pobierz jednostki, aby wyswietlic ich liste
        context['jednostki'] = Jednostka.objects.all()
    elif 'assign_units' in request.POST:
        # przejdz po kazdym uzytkowniku i dodaj wszystkie jednostki wskazane w formularzu
        for uzyt_id in request.POST.getlist('users'):
            uzytkownik = Uzytkownik.objects.get(id=uzyt_id)
            if request.POST['jednostka_1'] != '0': uzytkownik.jednostka.add(Jednostka.objects.get(id=request.POST['jednostka_1']))
            if request.POST['jednostka_2'] != '0': uzytkownik.jednostka.add(Jednostka.objects.get(id=request.POST['jednostka_2']))
            if request.POST['jednostka_3'] != '0': uzytkownik.jednostka.add(Jednostka.objects.get(id=request.POST['jednostka_3']))
            if request.POST['jednostka_4'] != '0': uzytkownik.jednostka.add(Jednostka.objects.get(id=request.POST['jednostka_4']))
            uzytkownik.save()
    elif 'remove_units' in request.POST:
        context['uzytkownik_odpiecie_jednostek'] = Uzytkownik.objects.get(id=request.POST.getlist('pick')[0])
    elif 'deassign_units' in request.POST:
        uzytkownik = Uzytkownik.objects.get(id=request.POST['uzytkownik'])
        
        #dokument.etykiety.clear()
        for jed in [ Jednostka.objects.get(id=jed) for jed in request.POST.getlist('jednostki') ]:
            uzytkownik.jednostka.remove(jed)
        uzytkownik.save()
        
        
        #etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('jednostki') ]
        #dokument.etykiety.add(*etykiety)        
        #dokument.save()

    return render(request, 'core/admin_users.html', context)

def admin_balance(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not request.user.is_admin:
        return redirect('access_denied')

    if 'add' in request.POST:
        bilans = BilansOtwarcia(rok=request.POST['rok'], kwota=request.POST['saldo'].replace(',', '.'))
        bilans.save()
   
    bilansy_otwarcia = BilansOtwarcia.objects.all()
    context = {'bilansy_otwarcia':bilansy_otwarcia}
    return render(request, 'core/admin_balance.html', context)

def admin_tags(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not request.user.is_admin:
        return redirect('access_denied')

    if 'add' in request.POST:
        etykieta = Etykieta(nazwa=request.POST['nazwa'], systemowa=False)
        etykieta.save()
   
    etykiety = Etykieta.objects.all()
    context  = {'etykiety':etykiety}
    return render(request, 'core/admin_tags.html', context)

def admin_doctitle(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not request.user.is_admin:
        return redirect('access_denied')
    
    if 'add' in request.POST:
        dekret = Dekret(numer=request.POST['numer'], opis=request.POST['opis'])
        dekret.save()    
    
    dekrety = Dekret.objects.all()
    context  = {'dekrety':dekrety}
    return render(request, 'core/admin_doctitle.html', context)    

def admin_invoices(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not request.user.is_admin:
        return redirect('access_denied')
    
    if 'add_numeracja' in request.POST:
        format_numeracji = NumeracjaFaktur(rok=int(request.POST['rok']), biezacy_numer=1, kategoria=request.POST['kategoria'])
        format_numeracji.save()
        
    if 'add_platnosc' in request.POST:
        sposob_platnosci = SposobPlatnosci(nazwa=request.POST['nazwa'], numer_konta=request.POST['numer_konta'])
        sposob_platnosci.save()
    
    formaty_numeracji = NumeracjaFaktur.objects.all()
    sposoby_platnosci = SposobPlatnosci.objects.all()
    context  = {'kategorie_numeracji':NumeracjaFaktur.CATEGORY_TYPE_CHOICES, 'formaty_numeracji':formaty_numeracji, 'sposoby_platnosci':sposoby_platnosci}
    return render(request, 'core/admin_invoices.html', context)    

def reports_cash(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        return redirect('access_denied')
    
    def create_pdf(request):
        
        def wrap_table(data):
            # print data on single pdf page
            t=Table(data, colWidths=(30, 60, 150, 320, 60, 60, 70))
            t.setStyle(TableStyle([('ALIGN',(1,1),(-2,-2),'RIGHT'),
                       #('TEXTCOLOR',(1,1),(-2,-2),colors.red),
                       ('VALIGN',(0,0),(0,-1),'TOP'),
                       #('TEXTCOLOR',(0,0),(0,-1),colors.blue),
                       ('ALIGN',(0,0),(-1,-1),'CENTER'),
                       ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                       ('FONTSIZE', (0,0), (-1,-1), 10),
                       ('FONTNAME', (0,0), (-1,-1), "FreeSerif"),
                       ('LEADING', (0,0), (-1,-1), 10),
                       #('TEXTCOLOR',(0,-1),(-1,-1),colors.green),
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                       ])) 
        
            t.wrapOn(p, width, height)
            t.drawOn(p, 50, table_y_pos, 0)
        
        response = HttpResponse(content_type='application/pdf')
        
        ###!!! trzeba zrobic radio nie checkbox
        raport        = RaportKasowy.objects.get(id=request.POST.getlist('pick')[0])
        numer_dok     = raport.numer_start
        saldo         = raport.saldo_start
        wydatki_suma  = decimal.Decimal(0.00)
        wplywy_suma   = decimal.Decimal(0.00)
        table_y_pos   = 500
        width, height = A4
        page_count    = 1

        response['Content-Disposition'] = 'attachment; filename="RK_' + str(raport.miesiac) + '_' + str(raport.rok) + '.pdf"'
        
        # Create the PDF object, using the response object as its "file."
        p = canvas.Canvas(response)
    
        # Draw things on the PDF. Here's where the PDF generation happens.
        # See the ReportLab documentation for the full list of functionality.
        p.setPageSize(landscape(A4))

        pdfmetrics.registerFont(TTFont('FreeSerif', 'FreeSerif.ttf'))
                
        p.setFont("FreeSerif", 12, leading = None)
        p.drawString(50,550,'Raport kasowy Hufiec Warszawa Ochota ' + MIESIACE[raport.miesiac -1][1] + ' ' + str(raport.rok) + ' strona ' + str(page_count))
        #p.drawString(200, 530, 'Saldo początkowe' + str(raport.saldo_start))
        p.line(20,545,820,545)
        
        header = ['Poz.', 'Data', 'Dowód Nr', 'Treść', 'Przychód', 'Rozchód', 'Saldo']
        data = [header]
        data.append(['', '', '', 'Saldo początkowe', '', '', str(raport.saldo_start)])
        total_dok = len(raport.dokument_set.all())
        for dok_enum in enumerate(raport.dokument_set.all().order_by('data_dokumentu')):
            dok = dok_enum[1]
            saldo += (dok.wplyw - dok.wydatek)
            data.append([str(numer_dok), str(dok.data_dokumentu), dok.numer, dok.opis, str(dok.wplyw), str(dok.wydatek), str(saldo)])
            numer_dok += 1
            wydatki_suma += dok.wydatek
            wplywy_suma += dok.wplyw
            table_y_pos -= 16
            if table_y_pos < 80:
                if dok_enum[0] + 1 == total_dok: 
                    p.setFont("FreeSerif", 10, leading = None)
                    p.drawString(550, table_y_pos - 16, 'RAZEM' + ' '*12 + str(wplywy_suma) + ' '*14 + str(wydatki_suma))
                    p.drawString(550, table_y_pos - 32, 'Saldo końcowe' + ' '*54 + str(saldo))
                wrap_table(data)
                data = [header]
                p.showPage()
                page_count  += 1
                table_y_pos = 520
                p.setFont("FreeSerif", 12, leading = None)
                p.drawString(50,550,'Raport kasowy Hufiec Warszawa Ochota ' + MIESIACE[raport.miesiac -1][1] + ' ' + str(raport.rok) + ' strona ' + str(page_count))
                p.line(20,545,820,545)
        if len(data) > 1:
            if dok_enum[0] + 1 == total_dok: 
                # alternatywna wersja: przyczepione do tabeli
                #data.append(['', '', '', 'RAZEM', str(wplywy_suma), str(wydatki_suma), ''])
                #data.append(['', '', '', 'Saldo końcowe', '', '', str(saldo)])
                p.setFont("FreeSerif", 10, leading = None)
                p.drawString(550, table_y_pos - 16, 'RAZEM' + ' '*12 + str(wplywy_suma) + ' '*14 + str(wydatki_suma))
                p.drawString(550, table_y_pos - 32, 'Saldo końcowe' + ' '*54 + str(saldo))
            wrap_table(data)
            p.showPage()
        
    
        # Close the PDF object cleanly, and we're done.
        p.save()
        
        return response 
    
    raporty = RaportKasowy.objects.order_by('rok', 'miesiac')
    
    lata = RaportKasowy.objects.order_by().values('rok').distinct()
    
    context = {'raporty':raporty, 'miesiace':MIESIACE, 'lata':sorted([d['rok'] for d in lata])}
    
    if 'add' in request.POST:
        raport_kasowy = RaportKasowy(miesiac=request.POST['miesiac'], rok=request.POST['rok'])
        raport_kasowy.save()
    
    # edycja wybanego raportu kasowego    
    if 'edit' in request.POST:
        # znajdz zaznaczony raport w bazie
        raport_id = request.POST.getlist('pick')[0]
        raport    = RaportKasowy.objects.get(id=raport_id)
        # zbierz wszystkie powiazane dokumenty
        context['edytowane_dokumenty_raport'] = raport.dokument_set.all()
    
    if 'delete_docs_report' in request.POST:
        for dok in range(len(request.POST.getlist('pick'))):
            dok_id   = request.POST.getlist('pick')[dok]
            dokument = Dokument.objects.get(id=dok_id)
            dokument.raport_kasowy = None
            dokument.save()
    
    # usuwanie wybranego raportu kasowego
    if 'delete' in request.POST:
        raport_id  = request.POST.getlist('pick')[0]
        raport_del = RaportKasowy.objects.get(id=raport_id)
        
        context['usuwany_raport'] = raport_del
        
    if 'delete_confirm' in request.POST:
        # usun powiazania dokumentow do raportu
        raport_id  = request.POST['usuwany_raport_id']
        raport_del = RaportKasowy.objects.get(id=raport_id)
        dokumenty  = raport_del.dokument_set.all()
        for dok in dokumenty:
            dok.raport_kasowy = None
            dok.save()
        raport_del.delete()
        # usun raport
    
    if 'recount' in request.POST:
        # okresla startowe saldo i numer porzadkowy dokumentu
        miesiac_start = int(request.POST['miesiac_start'])
        rok           = request.POST['rok']
        if miesiac_start == 1:
            saldo_start = BilansOtwarcia.objects.get(rok=rok).kwota
            numer_start = 1
        else:
            saldo_start = RaportKasowy.objects.get(miesiac=miesiac_start - 1, rok=rok).saldo_stop
            numer_start = RaportKasowy.objects.get(miesiac=miesiac_start - 1, rok=rok).numer_stop + 1
            
        # iterate through year recounting each month
        for report_month in range(miesiac_start, 13):
            
            ###!!! o co chodzi z tym try except tutaj?
            try:
                current_report = RaportKasowy.objects.get(miesiac=report_month, rok=rok)
            except ObjectDoesNotExist:
                break
            if current_report is None: break
            
            # ustaw saldo i numer startowe raportu
            current_report.saldo_start = balance = saldo_start
            current_report.numer_start  = number = numer_start
            # dodaj/odejmij kwote kazdego dokumentu powiazanego z danym raportem
            for dokument in current_report.dokument_set.all():
                balance += dokument.wplyw
                balance -= dokument.wydatek
                number += 1
            # ustaw koncowe saldo i numer na wyliczona wartosc
            current_report.saldo_stop = balance
            current_report.numer_stop = number - 1
            current_report.save()
            
            saldo_start = balance
            numer_start  = number
            
    if 'pdf' in request.POST:
        return create_pdf(request)

    return render(request, 'core/reports_cash.html', context)

def reports_balance(request):
    '''
    wyswietlanie sald jednostek
    '''
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        # ograniczenie wyboru jednostek
        jednostki = request.user.jednostka.all().order_by('nazwa')
    else:
        jednostki = Jednostka.objects.all().order_by('nazwa')

    context = {'jednostki': jednostki, 'typy_jednostek': Jednostka.TYP_JEDNOSTKI_CHOICES}
    return render(request, 'core/reports_balance.html', context)

def operations_view(request):
    def change_balance(operacja):
        # odwrocenie zmian na saldach ktore wprowadzila operacja
        
        if operacja.typ_operacji == 'TF':
            operacja.jednostka_zrodlowa.saldo += operacja.kwota
            operacja.jednostka_docelowa.saldo -= operacja.kwota
            operacja.jednostka_zrodlowa.save()
            operacja.jednostka_docelowa.save()     
        elif operacja.typ_operacji == 'BK':
            if operacja.jednostka_zrodlowa == None: 
                operacja.jednostka_docelowa.saldo -= operacja.kwota
                operacja.jednostka_docelowa.save() 
            else: 
                operacja.jednostka_zrodlowa.saldo += operacja.kwota
                operacja.jednostka_zrodlowa.save()
    
    def validate_data_search(request):
        error_log = []
        # sprawdzanie poprawnosci formatu daty
        for date in ['data_operacji_start', 'data_operacji_stop']:
            if not (re.search('^\d{4}-[0-1]\d-[0-3]\d$|^$', request.POST[date])): error_log.append('data')
        
        return error_log
    
    def search_operation(request):
        # wyszukiwanie operacji w bazie
        from django.db.models import Q
        kwargs    = {}
                
        if request.POST['jednostka'] != '0':
            jednostka = int(request.POST['jednostka'])
            args = ( Q( jednostka_docelowa = jednostka ) | Q( jednostka_zrodlowa = jednostka ), )
        else:
            args = ()
            
        if request.POST['opis'] != '':    
            kwargs['opis__contains'] = request.POST['opis']
            
        if request.POST['typ'] != '0':    
            kwargs['typ_operacji'] = request.POST['typ']
            
        if request.POST.getlist('etykieta'):
            kwargs['etykiety__in'] = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykieta') ]
        if request.POST['data_operacji_start'] != '':
            date_raw = request.POST['data_operacji_start'].split('-')
            start_date = datetime.date(int(date_raw[0]), int(date_raw[1]), int(date_raw[2]))
            date_raw = request.POST['data_operacji_stop'].split('-')
            end_date = datetime.date(int(date_raw[0]), int(date_raw[1]), int(date_raw[2]))
            kwargs['data_operacji__range'] = (start_date, end_date)
        if request.POST['kwota_start'] == '':
            kwota_start = decimal.Decimal(0.01)
        elif float(request.POST['kwota_start']) == 0.0:
            kwota_start = decimal.Decimal(0.01)
        else:
            kwota_start = decimal.Decimal(request.POST['kwota_start'])
        if request.POST['kwota_stop'] == '':
            kwota_stop = decimal.Decimal(1000000.0)
        else:
            kwota_stop = decimal.Decimal((request.POST['kwota_stop']))
        kwargs['kwota__range'] = (kwota_start, kwota_stop)    
                
        operacje = OperacjaSalda.objects.filter(*args, **kwargs)   
        
        return operacje
        
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        # ograniczenie wyboru jednostek
        jednostki = request.user.jednostka.all().order_by('nazwa')
    else:
        jednostki = Jednostka.objects.all().order_by('nazwa')

    etykiety = Etykieta.objects.all()
    today    = date.today()
    context  = {'typy_operacji':OperacjaSalda.OPERATION_TYPE_CHOICES, 'etykiety':etykiety, 'today':today, 'jednostki':jednostki}

    if 'search' in request.POST:
        error_log = validate_data_search(request)
        if not error_log:
            context['operacje'] = search_operation(request)
        else:
            context['error_log'] = error_log
    
    # wyswietlanie do potwierdzenia operacji ktore zostana usuniete
    elif 'delete' in request.POST:
        operacje = []
        for op_id in request.POST.getlist('pick'):
            operacje.append(OperacjaSalda.objects.get(id=op_id))
        context = {'usuwane_operacje': operacje}
        return render(request, 'core/operations_view.html', context)
    
    # usuwanie operacji po potwierdzeniu
    elif 'del_confirm' in request.POST:
        
        for op_id in request.POST.getlist('pick'):
            del_op = OperacjaSalda.objects.get(id=op_id)
            change_balance(del_op)    
            del_op.delete()
    
    else:
        context['default'] = 'default'
   
    return render(request, 'core/operations_view.html', context)

def operations_transfer(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        return redirect('access_denied')
    
    error_log = [] # inicjacja komunikatow bledow formularza
    if request.method == 'POST':
        
        # poczatek walidacji 
        if not request.POST['opis']: error_log.append('opis')
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['kwota'])): error_log.append('kwota')
        if 'kwota' not in error_log:
            if request.POST['kwota'] == '': error_log.append('kwota')
        # koniec walidacji
        
        if not error_log:      
            # znajdz jednostki uczestniczace w transferze
            jednostka_zrodlowa = Jednostka.objects.get(id=request.POST['jednostka_zrodlowa'])
            jednostka_docelowa = Jednostka.objects.get(id=request.POST['jednostka_docelowa'])
            uzytkownik         = Uzytkownik.objects.get(id=request.user.id)
            
            kwota = request.POST['kwota'].replace(',', '.')
            operacja = OperacjaSalda(opis=request.POST['opis'], kwota=kwota, uzytkownik=uzytkownik, jednostka_zrodlowa=jednostka_zrodlowa,
                                     jednostka_docelowa=jednostka_docelowa, typ_operacji='TF')
            operacja.save()

            # dodwanie etykiet
            etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety') ]
            operacja.etykiety.add(*etykiety)
            
            # dodaj/usun kwote ze wskazanych sald
            jednostka_zrodlowa.saldo -= decimal.Decimal(kwota)
            jednostka_docelowa.saldo += decimal.Decimal(kwota)
            jednostka_zrodlowa.save()
            jednostka_docelowa.save()
    
    jednostki = Jednostka.objects.all().order_by('nazwa')
    etykiety  = Etykieta.objects.all()
    context = {'jednostki':jednostki, 'etykiety':etykiety, 'error_log':error_log}
    return render(request, 'core/operations_transfer.html', context)

def operations_bank(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        return redirect('access_denied')
    
    error_log = [] # inicjacja komunikatow bledow formularza
    if request.method == 'POST':
        
        # poczatek walidacji 
        if not request.POST['opis']: error_log.append('opis')
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['kwota'])): error_log.append('kwota')
        if 'kwota' not in error_log:
            if request.POST['kwota'] == '': error_log.append('kwota')
        # koniec walidacji
        
        if not error_log:
            
            # znajdz jednostke uczestniczaca w transferze
            jednostka  = Jednostka.objects.get(id=request.POST['jednostka'])
            uzytkownik = Uzytkownik.objects.get(id=request.user.id)
            
            kwota = request.POST['kwota'].replace(',', '.')
            akcja = request.POST['akcja']
            # jezeli uznanie to jednostka wpisywana w pole jednostkazrodlowa, inaczej w pole jednostka_docelowa (istotne do rozpoznania typu akcji przy edycji/usuwaniu/wyswietlaniu)
            if akcja == 'uznanie': operacja = OperacjaSalda(opis=request.POST['opis'], kwota=kwota, uzytkownik=uzytkownik, jednostka_docelowa=jednostka, typ_operacji='BK')
            elif akcja == 'obciazenie': operacja = OperacjaSalda(opis=request.POST['opis'], kwota=kwota, uzytkownik=uzytkownik, jednostka_zrodlowa=jednostka, typ_operacji='BK')
            operacja.save()

            # dodwanie etykiet
            etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety') ]
            operacja.etykiety.add(*etykiety)
            
            # dodaj/usun kwote zgodnie z akcja
            if akcja == 'uznanie': jednostka.saldo += decimal.Decimal(kwota)
            elif akcja == 'obciazenie': jednostka.saldo -= decimal.Decimal(kwota) 
            jednostka.save()
    
    jednostki = Jednostka.objects.all().order_by('nazwa')
    etykiety  = Etykieta.objects.all()
    context = {'jednostki':jednostki, 'etykiety':etykiety, 'error_log':error_log}
    return render(request, 'core/operations_bank.html', context)

def operations_many(request):
    def validate_data(request):
        error_log = [] # inicjacja komunikatow bledow formularza
        # poczatek walidacji 
        if len(request.POST.getlist('jednostki')) == 0: error_log.append('jednostki')
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['kwota'])): error_log.append('kwota')
        if (request.POST['jednostka_beneficjent'] == '0') and (request.POST['akcja'] == '0'): error_log.append('dzialanie') 
        # koniec walidacji
        return error_log
    
    def validate_data_submit(request, jed):
        if not (re.search('^\d+([.,]\d{1,2})?$|^$', request.POST.getlist('kwota')[jed])): return True
        if request.POST.getlist('kwota')[jed] == '': return True
        if request.POST.getlist('opis')[jed] == '': return True
    
    def select_units(request):
        wybrane_jednostki = set()
        lista_jednostek = request.POST.getlist('jednostki')
        if 'WSZ' in lista_jednostek: wybrane_jednostki = wybrane_jednostki | set(Jednostka.objects.all())
        if 'PDS' in lista_jednostek: wybrane_jednostki = wybrane_jednostki | set(Jednostka.objects.filter(typ_jednostki='PDS'))
        if 'NPD' in lista_jednostek: wybrane_jednostki = wybrane_jednostki | set(Jednostka.objects.filter(typ_jednostki='NPD'))
        if 'SZP' in lista_jednostek: wybrane_jednostki = wybrane_jednostki | set(Jednostka.objects.filter(typ_jednostki='SZP'))
        if 'ZSH' in lista_jednostek: wybrane_jednostki = wybrane_jednostki | set(Jednostka.objects.filter(typ_jednostki='ZSH'))
        for jed_id in lista_jednostek:
            if jed_id not in ['WSZ', 'PDS', 'NPD', 'SZP', 'ZSH']: wybrane_jednostki.add(Jednostka.objects.get(id=jed_id))
        
        return wybrane_jednostki        
      
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        return redirect('access_denied')
    
    jednostki = Jednostka.objects.all().order_by('nazwa')
    etykiety  = Etykieta.objects.all()
    context = {'jednostki':jednostki, 'pokaz_jednostki':int(len(jednostki)/3), 'etykiety':etykiety}
    
    if 'jednostki_wybrane' in request.POST:
        context['jednostki_wybrane']     = []
        context['etykiety_wybrane']      = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety_wybrane') ]
        jednostka_beneficjent            = Jednostka.objects.get(id=request.POST['jednostka_beneficjent']) if request.POST['jednostka_beneficjent'] != '0' else ''
        context['jednostka_beneficjent'] = jednostka_beneficjent
        context['akcja']                 = request.POST['akcja']
        uzytkownik                       = Uzytkownik.objects.get(id=request.user.id)
        
        for jed in range(len(request.POST.getlist('jednostki_wybrane'))):
            jed_id = request.POST.getlist('jednostki_wybrane')[jed]
            if not validate_data_submit(request, jed): # weryfikacja czy dane wejsciowe zawieraja bledy
                jednostka = Jednostka.objects.get(id=jed_id)
                kwota     = request.POST.getlist('kwota')[jed].replace(',', '.')
                opis      = request.POST.getlist('opis')[jed]
                # dodaj operacje
                if jednostka_beneficjent: # dodawana jest operacja transferu
                    operacja = OperacjaSalda(opis=opis, kwota=kwota, uzytkownik=uzytkownik, 
                                             jednostka_zrodlowa=jednostka, jednostka_docelowa=jednostka_beneficjent, typ_operacji='TF')
                    operacja.save()
                    # dodaj/usun kwote ze wskazanych sald
                    jednostka.saldo -= decimal.Decimal(kwota)
                    jednostka_beneficjent.saldo += decimal.Decimal(kwota)
                    jednostka.save()
                    jednostka_beneficjent.save()
                else: # dodawana jest operacja bankowa
                    akcja = request.POST['akcja']
                    if akcja == 'uznanie': operacja = OperacjaSalda(opis=opis, kwota=kwota, uzytkownik=uzytkownik, jednostka_docelowa=jednostka, typ_operacji='BK')
                    elif akcja == 'obciazenie': operacja = OperacjaSalda(opis=opis, kwota=kwota, uzytkownik=uzytkownik, jednostka_zrodlowa=jednostka, typ_operacji='BK')
                    print(kwota, jed, jed_id)
                    operacja.save()
                    # dodaj/usun kwote zgodnie z akcja
                    if akcja == 'uznanie': jednostka.saldo += decimal.Decimal(kwota)
                    elif akcja == 'obciazenie': jednostka.saldo -= decimal.Decimal(kwota) 
                    jednostka.save()
                    # dodwanie etykiet
                etykiety = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety_wybrane') ]
                operacja.etykiety.add(*etykiety)
            else:
                # zwroc operacje do poprawki
                context['jednostki_wybrane'].append(Jednostka.objects.get(id=jed_id))
                context['error_log'] = 'error_log'
                
    elif request.method == 'POST':
        error_log = validate_data(request)
        if not error_log:
            context['etykiety_wybrane']      = [ Etykieta.objects.get(id=ety) for ety in request.POST.getlist('etykiety') ]
            context['jednostka_beneficjent'] = Jednostka.objects.get(id=request.POST['jednostka_beneficjent']) if request.POST['jednostka_beneficjent'] != '0' else ''
            context['kwota']                 = request.POST['kwota']
            context['opis']                  = request.POST['opis']
            context['akcja']                 = request.POST['akcja']
            context['jednostki_wybrane']     = select_units(request)

    return render(request, 'core/operations_many.html', context)

def invoices(request):
    
    def create_invoice_pdf(request, faktura_id):
        
        THOUSANDS_DICT = {'1':'tysiąc', '2':'dwa tysiące', '3':'trzy tysiące', '4':'cztery tysiące', '5':'pięć tysięcy',
                  '6':'sześć tysięcy', '7':'siedem tysięcy', '8':'osiem tysięcy', '9':'dziewięć tysięcy', '0':''}
        HUNDREADS_DICT = {'1':'sto', '2':'dwieście', '3':'trzysta', '4':'czterysta','5':'pięćset', '6':'sześćset',
                          '7':'siedemset', '8':'osiemset','9':'dziewięćset', '0':''}
        TENS_DICT      = {'2':'dwadzieścia', '3':'trzydzieści', '4':'czterdzieści', '5':'pięćdziesiąt', '6':'sześćdziesiąt',
                          '7':'siedemdziesiąt', '8':'osiemdziesiąt', '9':'dziewięćdziesiąt'}
        UNITS_DICT     = {'01':'jeden', '02':'dwa', '03':'trzy', '04':'cztery', '05':'pięć', '06':'sześć', '07':'siedem', '08':'osiem',
                          '09':'dziewięć', '10':'dziesięć', '11':'jedenaście', '12':'dwanaście', '13':'trzynaście', '14':'czternaście',
                          '15':'piętnaście', '16':'szesnaście', '17':'siedemnaście', '18':'osiemnaście', '19':'dziewiętnaście', '00':''}
        
        def convert_amount2string(amount):
            
            amount_int = amount
            if amount_int == '00':
                return 'zero'
            amount_string = []
            
            if len(amount_int) > 1:
                amount_string.append(UNITS_DICT['0' + amount_int[-1]] if int(amount_int[-2]) > 1 else '')
                amount_string.append(TENS_DICT[amount_int[-2]] if int(amount_int[-2]) > 1 else UNITS_DICT[amount_int[-2:]])
            else:
                amount_string.append(UNITS_DICT['0' + amount_int[-1]])
            if len(amount_int) > 2:
                amount_string.append(HUNDREADS_DICT[amount_int[-3]])
            if len(amount_int) > 3:
                amount_string.append(THOUSANDS_DICT[amount_int[-4]])
                
            return ' '.join(s for s in reversed(amount_string) if s != '')
                
        def divide_title_into_lines(tytul):
            # szerokosc max 32 znaki
            tytul_divided = ''
            text_buffer = ''
            buffer_index = 0
            last_space = 0
            for char in tytul:
                if char == ' ':
                    last_space = buffer_index
                if buffer_index > 32:
                    tytul_divided += (text_buffer[0:last_space] + '\n')
                    text_buffer = text_buffer[last_space:]
                    buffer_index = len(text_buffer)
                    last_space = 0
                text_buffer += char
                buffer_index += 1
            tytul_divided += text_buffer
            
            return tytul_divided
        
        response = HttpResponse(content_type='application/pdf')
        faktura = Faktura.objects.get(id=faktura_id)
        response['Content-Disposition'] = 'attachment; filename="' + str(faktura.numer) + '.pdf"'
        
        invoice_id  = faktura.numer
        parent_name = faktura.nabywca_nazwa
        address     = faktura.nabywca_adres
        NIP         = faktura.nabywca_nip
        tytul       = divide_title_into_lines(faktura.tytul.replace('\r\n', ''))
        # kwoty
        amount          = str(faktura.kwota)
        tax             = decimal.Decimal(faktura.stawka_vat if faktura.stawka_vat != 'ZW' else 0.00) / 100
        tax_amount      = str(round(faktura.kwota * tax, 2))
        amount_with_tax = str(round(faktura.kwota + faktura.kwota * tax, 2))
        stawka_vat      = faktura.stawka_vat.lower() if faktura.stawka_vat == 'ZW' else str(int(faktura.stawka_vat)) + '%'
        
        #def make_invoice(invoice_id, dirpath, child_name, parent_name, address, NIP, amount, camp_date):
        # Create the PDF object, using the response object as its "file."
        p = canvas.Canvas(response)
        
        # Draw things on the PDF. Here's where the PDF generation happens.
        # See the ReportLab documentation for the full list of functionality.
        p.setPageSize(letter)
        
        pdfmetrics.registerFont(TTFont('FreeSerif', 'FreeSerif.ttf'))
        #p.setFont("Helvetica", 40)
        
        # data wystawienia
        p.setFont("FreeSerif", 12, leading = None)
        p.drawString(450,770,"Miejscowość: Warszawa")
        p.drawString(450,758,"Data wystawienia: " + str(faktura.data_wystawienia))
        p.drawString(450,746,"Data sprzedaży: " + str(faktura.data_wystawienia))
        
        # numer faktury
        p.setFont("FreeSerif", 16, leading = None)
        p.drawString(250,730,"Faktura VAT")
        p.setFont("FreeSerif", 14, leading = None)
        p.drawString(250,710, invoice_id)
        
        # sprzedawca
        p.drawString(20,670,"Sprzedawca:")
        p.line(20,665,120,665)
        p.drawString(20,650,"Chorągiew Stołeczna ZHP")
        p.drawString(20,634,"ul. Piaskowa 4, 01-067 Warszawa")
        p.drawString(20,618,"NIP: 527-252-61-38")
        p.drawString(20,602,"Hufiec Warszawa-Ochota")
        
        # nabywca
        p.drawString(300,670,"Nabywca:")
        p.line(300,665,400,665)
        #if len(parent_name) > 32:
        #    p.setFont("FreeSerif", 12, leading = None)
        #    print('adjusted', invoice_id)
        parent_name = parent_name.title()
        p.drawString(300,650, parent_name)
        p.setFont("FreeSerif", 14, leading = None)
        p.drawString(300,634, address)
        p.drawString(300,618,"NIP: " + NIP)
        
        # artykuly
        p.setFont("FreeSerif", 12, leading = None)
        p.line(20,590,600,590)
        header = ['L.p.', 'Nazwa towaru\nlub usługi', 'Symbol\nPKWiU', 'Miara', 'Ilość', 'Cena jed.\nbez podatku', 'Wartość\nbez podatku', 'Stawka\npodatku', 'Kwota\npodatku', 'Wartość wraz\nz podatkiem']
        data   = [header]
        
        data.append(['1', tytul, '', 'szt.', '1', amount, amount, stawka_vat, tax_amount, amount_with_tax])
        data.append(['', '', '', '', '', '', amount, stawka_vat, tax_amount, amount_with_tax])
        data.append(['', '', '', '', '', 'RAZEM', amount, stawka_vat, tax_amount, amount_with_tax])
        
        t=Table(data)
        t.setStyle(TableStyle([
                        ('ALIGN',(1,1),(-2,-2),'RIGHT'),
                       #('TEXTCOLOR',(1,1),(-2,-2),colors.red),
                       ('VALIGN',(0,0),(0,-1),'TOP'),
                       #('TEXTCOLOR',(0,0),(0,-1),colors.blue),
                       ('ALIGN',(0,0),(-1,-1),'CENTER'),
                       ('VALIGN',(0,-1),(-1,-1),'MIDDLE'),
                       ('FONTSIZE', (0,0), (-1,-1), 10),
                       ('FONTNAME', (0,0), (-1,-1), "FreeSerif"),
                       ('LEADING', (0,0), (-1,-1), 10),
                       #('TEXTCOLOR',(0,-1),(-1,-1),colors.green),
                       ('INNERGRID', (0,0), (-1,-3), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-3), 0.25, colors.black),
                       ('INNERGRID', (-4,-2), (-1,-1), 0.25, colors.black),
                       ('BOX', (-4,-2), (-1,-1), 0.25, colors.black),
                       ('INNERGRID', (-5,-1), (-1,-1), 0.25, colors.black),
                       ('BOX', (-5,-1), (-1,-1), 0.25, colors.black),
               ]))


        width, height = A4
        t.wrapOn(p, width, height)
        t.drawOn(p, 20, 470, 0)
        
        # zaplata
        p.drawString(20, 440,"Do zapłaty: " + amount_with_tax)
        p.line(20,435,150,435)
        p.setFont("FreeSerif", 12, leading = None)
        p.drawString(20, 420,"Słownie: " + convert_amount2string(amount_with_tax.split('.')[0]) + " złotych, " + convert_amount2string(amount_with_tax.split('.')[1]) + " groszy")
        
        if faktura.sposob_platnosci.numer_konta == '-':
            p.drawString(20, 400,"Sposób płatności: gotówka") # platnosc gotowka
        else:
            p.drawString(20, 400,"Sposób płatności: zapłacono przelewem") # przelew
        
        p.drawString(20, 385,"Nr konta: " + faktura.sposob_platnosci.numer_konta)
        p.drawString(20, 370,"Termin zapłaty: " + str(faktura.data_wystawienia))
        
        # adnotacje
        p.setFont("FreeSerif", 10, leading = None)
        if faktura.stawka_vat == 'ZW':
            p.drawString(20, 335,"UWAGI: Zwolnienie z VAT na podstawie art. 43 ust. 1 pkt. 21 ustawy o VAT (Dz. U. z 2004 r. Nr 54, poz. 535 z późn. zm.).")
        
        # podpis wystawcy
        p.drawString(400,270,"phm. Krzysztof Szczepaniak")
        p.line(400,260,520,260)
        p.setFont("FreeSerif", 10, leading = None)
        p.drawString(400,250,"Podpis osoby upoważnionej")
        p.drawString(400,240,"do wystawienia faktury")
        
        # Close the PDF object cleanly, and we're done.
        p.showPage()
        p.save()
        
        return response
    
    if not request.user.is_authenticated():
        return redirect('auth_login')
    elif not (request.user.is_staff or request.user.is_admin):
        # ograniczenie wyboru jednostek
        jednostki = request.user.jednostka.all().order_by('nazwa')
    else:
        jednostki = Jednostka.objects.all().order_by('nazwa')
        
    faktury = Faktura.objects.filter(jednostka__in=jednostki)
    context = {'faktury': faktury}
    
    if 'approve' in request.POST:
        context['zatwierdzane_faktury'] = []
        context['numeracje']            = NumeracjaFaktur.objects.all()
        context['sposoby_platnosci']    = SposobPlatnosci.objects.all()
        for fakt_id in request.POST.getlist('pick'):
            appr_fakt = Faktura.objects.get(id=fakt_id)
            context['zatwierdzane_faktury'].append(appr_fakt)
    
    if 'approve_confirm' in request.POST:
        numeracja        = NumeracjaFaktur.objects.get(id=request.POST['numeracja'])
        sposob_platnosci = SposobPlatnosci.objects.get(id=request.POST['sposob_platnosci'])
        for fakt_id in request.POST.getlist('pick'):
            appr_fakt                  = Faktura.objects.get(id=fakt_id)
            appr_fakt.status           = 'ZT'
            appr_fakt.data_wystawienia = date.today()
            appr_fakt.numer            = str(numeracja.biezacy_numer) + '/034/' + numeracja.kategoria + '/' + str(numeracja.rok)
            appr_fakt.sposob_platnosci = sposob_platnosci  
            appr_fakt.save()
            numeracja.biezacy_numer += 1
            numeracja.save()
            
    if 'delete' in request.POST:
        error_log_delete = ''
        for fakt_id in request.POST.getlist('pick'):
            del_fakt = Faktura.objects.get(id=fakt_id)
            if del_fakt.status != 'ZT':
                del_fakt.delete()
            else:
                error_log_delete = 'usuwanie_zatwierdzonej'
        if error_log_delete:
            context['error_log_delete'] = error_log_delete
    
    pdfs = [ key for key in request.POST.keys() if re.match('pdf_\d+', key)]
    if pdfs:
        return create_invoice_pdf(request, pdfs[0].replace('pdf_', ''))
    
    return render(request, 'core/invoices.html', context)

def invoices_upload(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    
    import unicodecsv as csv
    context = {}
    
    def add_invoice(faktura, mode):
        
        def parse_vat(stawka_vat):
            stawka_vat = stawka_vat.strip()
            if (stawka_vat == 'zw' or stawka_vat == 'ZW'):
                return 'ZW'
            elif (stawka_vat == '5' or stawka_vat == '05'):
                return '05'
            elif (stawka_vat == '8' or stawka_vat == '08'):
                return '08'
            elif (stawka_vat == '23' or stawka_vat == '23'):
                return '23'
        
        if re.search(';', str(faktura[0])):
            dane_faktury = str(faktura[0]).split(';')
            tytul = dane_faktury[5]
        elif re.search(',', str(faktura)):
            dane_faktury = faktura
            tytul = ''.join(dane_faktury[5:])
        
        faktura_nowa = Faktura(numer='', data_wystawienia=None, nabywca_nazwa=dane_faktury[0], nabywca_adres=dane_faktury[1], nabywca_nip=dane_faktury[2], kwota=float(dane_faktury[3]), 
                               stawka_vat=parse_vat(dane_faktury[4]), tytul=tytul, sposob_platnosci=None, uwagi='', status='ZG', uzytkownik=request.user, 
                               jednostka=request.user.jednostka.all()[0])
        if mode == 'add':
            faktura_nowa.save()
        elif mode == 'verify':
            return faktura_nowa
    
    if 'upload_verify' in request.POST:
        
        faktury = []
        plik_faktur = csv.reader(request.FILES['plik_faktur'], encoding='utf-8')
        for faktura in plik_faktur:
            if 'nabywca_nazwa' in str(faktura):
                continue
            faktury.append(add_invoice(faktura, 'verify'))
            
        context['faktury'] = faktury
    
    if 'upload' in request.POST:
        
        for faktura in request.POST.getlist('faktury'):
            add_invoice([faktura], 'add')

    return render(request, 'core/invoices_upload.html', context)

def invoices_single(request):
    if not request.user.is_authenticated():
        return redirect('auth_login')
    
    sposoby_platnosci = SposobPlatnosci.objects.all()
    context = {'sposoby_platnosci':sposoby_platnosci, 'stawki_vat':Faktura.VAT_TYPE_CHOICES}
    
    if 'send' in request.POST:
        error_log = []
        if (not request.POST['nabywca_nazwa']) or (not request.POST['nabywca_adres']) or (not re.search('^\d+([.,]\d{1,2})?$|^$', request.POST['kwota'])) or (not request.POST['tytul']):
            error_log.append('error') 
            context['error_log'] = error_log
        
        if not error_log:
            sposob_platnosci = SposobPlatnosci.objects.get(id=request.POST['sposob_platnosci'])
            faktura = Faktura(numer='', data_wystawienia=None, nabywca_nazwa=request.POST['nabywca_nazwa'], nabywca_adres=request.POST['nabywca_adres'], nabywca_nip=request.POST['nabywca_nip'], 
                               kwota=float(request.POST['kwota'].replace(',', '.')), stawka_vat=request.POST['stawka_vat'], tytul=request.POST['tytul'], sposob_platnosci=sposob_platnosci,
                               uwagi='', status='ZG', uzytkownik=request.user, jednostka=request.user.jednostka.all()[0])
            faktura.save()
    
    return render(request, 'core/invoices_single.html', context)

