from django.core.management.base import BaseCommand, CommandError
from core.models import Jednostka

DATADIR = 'E:/workspace/Phoenicia21/data/'

class Command(BaseCommand):

    def handle(self, *args, **options):
        units_file = open(DATADIR + 'table_units.csv', 'r', encoding='utf-8')
        data       = units_file.readline()
        
        for unit_data in data.split('>'):
            unit = unit_data.split('|')
            if len(unit) > 1:
                print('Uploading', unit)
                jednostka = Jednostka(nazwa=unit[1], saldo=float(unit[2]),
                                      typ_jednostki='PDS', aktywna=True) 
            jednostka.save()
    