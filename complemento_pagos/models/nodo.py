# -*- encoding: utf-8 -*-

from lxml import etree
from lxml.objectify import fromstring

class Nodo:
    def __init__(self, nombre, atributos={}, padre=None, valor=None):
        self.nombre = nombre
        self.atributos = atributos or {}
        self.hijos = []
        if padre:
            padre.append(self)
        if not valor is None:
            self.hijos.append(valor)
        
    def append(self, *hijos):
        for hijo in hijos:
            self.hijos.append(hijo)
        return self
                
    def __getitem__(self, key):
        return self.atributos[key]
        
    def __setitem__(self, key, value):
        self.atributos[key] = value
        
    def xml_escape(self, cadena):
        cadena = cadena.replace("&", "--ampersand--")
        cadena = cadena.replace('"', "&quot;")
        cadena = cadena.replace('<', "&lt;")
        cadena = cadena.replace('>', "&gt;")
        cadena = cadena.replace("'", "&apos;")
        cadena = cadena.replace('--ampersand--', "&amp;")
        return cadena
    
    def toxml(self, header=True):
        if len(self.hijos) == 0 and len(self.atributos) == 0:
            return ""
        texto = "<"+self.nombre
        for atributo,valor in self.atributos.items():
            try:
                valor = str(valor)
            except:
                pass
            if valor:
                texto += " "+atributo+"="+'"'+self.xml_escape(valor)+'"'
        if not self.hijos:
            texto += "/>"
        else:
            texto += ">"
            for hijo in self.hijos:
                if isinstance(hijo, Nodo):
                    hijo = hijo.toxml(header=False)
                elif type(hijo) != unicode:
                    try:
                        hijo = str(hijo)
                        hijo = self.xml_escape(hijo)
                    except:
                        print("******hijo malo",type(hijo))
                else:
                    hijo = self.xml_escape(hijo)
                texto += hijo
            texto += "</"+self.nombre+">"
        if header:
            texto = '<?xml version="1.0" encoding="UTF-8"?>' + texto
        return texto

        
        
