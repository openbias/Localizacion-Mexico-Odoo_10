# -*- coding: utf-8 -*-

from lxml import etree
import suds
from suds.client import Client
import xmltodict, json
import time

import logging
_logger = logging.getLogger(__name__)

try:
    import feedparser
except ImportError:
    pass

def rate_retrieve_old():
    banxico_rss_url = "http://www.banxico.org.mx/rsscb/rss?BMXC_canal=pagos&BMXC_idioma=es" 
    feed = feedparser.parse(banxico_rss_url)
    rate = 0.0
    for f in feed.entries:
        rate = f and f.cb_exchangerate or 0.0
    return rate

def rate_retrieve_cop():
    WSDL_URL = 'https://www.superfinanciera.gov.co/SuperfinancieraWebServiceTRM/TCRMServicesWebService/TCRMServicesWebService?WSDL'
    date = time.strftime('%Y-%m-%d')
    try:
        client = Client(WSDL_URL, location=WSDL_URL, faults=True)
        soapresp =  client.service.queryTCRM(date)
        if soapresp["success"] and soapresp["value"]:
            return {"COP": soapresp["value"]}
        return False
    except Exception as e:
        return False
    return False


def rate_retrieve():
    hostname = 'http://www.banxico.org.mx:80/DgieWSWeb/DgieWS?WSDL'
    client = Client(hostname, cache=None, timeout=40)
    print "clientclient", client
    tipoCambioResponse = client.service.tiposDeCambioBanxico()
    parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
    objroot = etree.fromstring(tipoCambioResponse.encode("utf-8"), parser=parser)
    namespaces = {
        'http://www.SDMX.org/resources/SDMXML/schemas/v1_0/message': None,
        'http://www.banxico.org.mx/structure/key_families/dgie/sie/series/compact': 'ns_bm',
        'http://www.SDMX.org/resources/SDMXML/schemas/v1_0/compact': 'ns_compact'
    }
    datas = xmltodict.parse(etree.tostring(objroot), process_namespaces=True, namespaces=namespaces)
    tipoCambio = {}
    if datas and datas.has_key('CompactData') \
                and datas['CompactData'].get('ns_bm:DataSet') \
                and datas['CompactData']['ns_bm:DataSet'].get('ns_bm:Series'):

        for serie in datas['CompactData']['ns_bm:DataSet']['ns_bm:Series']:
            if serie.get('@IDSERIE') == 'SF60653':
                tipoCambio['MXN'] = float(serie['ns_bm:Obs'].get('@OBS_VALUE', '0.0'))
            if serie.get('@IDSERIE') == 'SF46410':
                tipoCambio['EUR'] = float(serie['ns_bm:Obs'].get('@OBS_VALUE', '0.0'))

            # tipoCambio.append({
            #     'TITULO': serie.get('@TITULO').encode("utf-8"),
            #     'IDSERIE': serie.get('@IDSERIE').encode("utf-8"),
            #     'BANXICO_FREQ': serie.get('@BANXICO_FREQ').encode("utf-8"),
            #     'BANXICO_FIGURE_TYPE': serie.get('@BANXICO_FIGURE_TYPE').encode("utf-8"),
            #     'BANXICO_UNIT_TYPE': serie.get('@BANXICO_UNIT_TYPE').encode("utf-8"),
            #     'TIME_PERIOD': serie['ns_bm:Obs'].get('@TIME_PERIOD'),
            #     'OBS_VALUE': serie['ns_bm:Obs'].get('@OBS_VALUE')
            #     })

    if tipoCambio.get("MXN") and tipoCambio.get("EUR"):
        tipoCambio["EUR"] = tipoCambio["MXN"] / tipoCambio["EUR"]

    rate_cop = rate_retrieve_cop()
    if rate_cop:
        tipoCambio.update(rate_cop)

    return tipoCambio

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: