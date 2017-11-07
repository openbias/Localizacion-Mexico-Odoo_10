# -*- coding: utf-8 -*-


catcfdi = {
    'formaPago': ['01','02','03','04','05','06','08','12','13','14','15','17','23','24','25','26','27','28','29','30','99'],
    'metodoPago': ['PUE', 'PPD'],
    'impuesto': ['001','002','003'],    
    'regimenFiscal': ['601','603','605','606','608','609','610','611','612','614','616','620','621','622','623','624','628','607','629','630','615'],
    'ingreso': ['I','E','T','N','P'],
    'usoCdfi': ['G01','G02','G03','I01','I02','I03','I04','I05','I06','I07','I08','D01','D02','D03','D04','D05','D06','D07','D08','D09','D10','P01']
}

def valida_catcfdi(cat, value):
    res = False
    if catcfdi.get(cat, False):
        if value in catcfdi[cat]:
            res = True
    return res



