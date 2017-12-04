# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import json
import csv
import os
import inspect

import logging
logging.basicConfig(level=logging.INFO)

class AltaCatalogosCFDI(models.TransientModel):
    _name = 'cf.mx.alta.catalogos.wizard'
    _description = 'Alta Catalogos CFDI'

    @api.multi
    def action_alta_catalogos(self):
        logging.info(' Inicia Alta Catalogos')
        models = [
            'cfd_mx.unidadesmedida',
            'cfd_mx.prodserv',
            'res.country.state.municipio',
            'res.country.state.ciudad',
            'res.country.state.cp'
        ]
        for model in models:
            model_name = model.replace('.', '_')
            logging.info(' Model: -- %s'%model_name )

            model_obj = self.env[model]
            fname = '/../data/json/%s.json' % model
            current_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))        
            path =  current_path+fname
            jdatas = json.load(open(path))
            for indx, data in enumerate(jdatas):
                header = data.keys()
                body = data.values()
                r = model_obj.with_context(noupdate=True).load(header, [body])
                logging.info(' Model: -- %s, Res: %s - %s'%(model_name, indx, r) )
                if r.get("messages"):
                    logging.info(' Model: -- %s, Res: %s - %s'%(model_name, indx, r) )
                self._cr.commit()
        return True


class TipoRelacion(models.Model):
    _name = "cfd_mx.tiporelacion"

    name = fields.Char("Descripcion", size=128)
    clave = fields.Char(string="Clave", help="Clave Tipo Relacion")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(TipoRelacion, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class UsoCfdi(models.Model):
    _name = "cfd_mx.usocfdi"

    name = fields.Char("Descripcion", size=128)
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(UsoCfdi, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()






class MetodoPago(models.Model):
    _name = "cfd_mx.metodopago"

    name = fields.Char("Descripcion", size=128, required=True, default="")
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(MetodoPago, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class Regimen(models.Model):
    _name = "cfd_mx.regimen"

    name = fields.Char("Regimen Fiscal", size=128)
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    persona_fisica = fields.Boolean(string="Aplica Persona Fisica")
    persona_moral = fields.Boolean(string="Aplica Persona Moral")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(Regimen, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()








class FormaPago(models.Model):
    _name = 'cfd_mx.formapago'

    name = fields.Char(string="Descripcion", size=64, required=True, default="")
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    nombre_banco_ext = fields.Boolean(string="Nombre Banco", help="Nombre del Banco emisor de la cuenta ordenante en caso de extranjero")
    banco = fields.Boolean(string="Banco", help="Activar este checkbox para que pregunte número de cuenta")
    no_operacion = fields.Boolean(string="Num. Operacion", default=False)
    rfc_ordenante = fields.Boolean(string="RFC Ordenante", default=False)
    cuenta_ordenante = fields.Boolean(string="Cuenta Ordenante", default=False)
    patron_ordenante = fields.Char(string="Patron Ordenante", default='')
    rfc_beneficiario = fields.Boolean(string="RFC Beneficiario", default=False)
    cuenta_beneficiario = fields.Boolean(string="Cuenta Beneficiario", default=False)
    patron_beneficiario = fields.Char(string="Patron Beneficiario", default='')
    tipo_cadena = fields.Boolean(string="Tipo Cadena", default=False)
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')
    pos_metodo = fields.Many2one('account.journal', domain=[('journal_user', '=', 1)],
            string="Metodo de pago del TPV")
    conta_elect = fields.Boolean("Es Contabilidad Electronica?", default=False)


    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_prod_ids = self.search([('clave', 'ilike', name)] + args, limit=limit)
            if cod_prod_ids: recs += cod_prod_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class ClaveProdServ(models.Model):
    _name = 'cfd_mx.prodserv'
    _description = 'Clave del Producto o Servicio'

    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    name = fields.Char("Descripcion", size=264, required=True, default="")
    incluir_iva = fields.Char(string='Incluir IVA trasladado')
    incluir_ieps = fields.Char(string='Incluir IVA trasladado')
    complemento = fields.Char("Complemento Incluir", required=False, default="")
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')
    similares = fields.Char("Palabras Similares", required=False, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_prod_ids = self.search([('clave', 'ilike', name)] + args, limit=limit)
            if cod_prod_ids: recs += cod_prod_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class UnidadesMedida(models.Model):
    _name = 'cfd_mx.unidadesmedida'
    _description = u"Catalogo de unidades de medida para los conceptos en el CFDI."

    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    name = fields.Char(string="Nombre", size=264, required=True, default="")
    descripcion = fields.Char("Descripcion", required=False, default="")
    nota = fields.Char("Nota", required=False, default="")
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')
    simbolo = fields.Char("Simbolo", required=False, default="")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            cod_prod_ids = self.search([('clave', 'ilike', name)] + args, limit=limit)
            if cod_prod_ids: recs += cod_prod_ids

            search_domain = [('name', operator, name)]
            if recs.ids:
                search_domain.append(('id', 'not in', recs.ids))
            name_ids = self.search(search_domain + args, limit=limit)
            if name_ids: recs += name_ids

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

class Aduana(models.Model):
    _name = "cfd_mx.aduana"

    name = fields.Char("Regimen Fiscal", size=128)
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    from_date = fields.Date(string='Fecha Inicial')
    to_date = fields.Date(string='Fecha Inicial')

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.clave, rec.name or '')))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = super(Aduana, self).name_search(name, args=args, operator=operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('clave', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class Addendas(models.Model):
    _name = 'cfd_mx.conf_addenda'

    model_selection = fields.Selection(selection=[])
    partner_ids = fields.Many2many('res.partner', string="Clientes", domain=[('customer', '=', True )] )

    def create_addenda(self, invoices):
        context = self._context or {}
        cfd_addenda = self.model_selection
        if hasattr(self, '%s_create_addenda' % cfd_addenda):
            return getattr(self, '%s_create_addenda' % cfd_addenda)(invoices)
        else:
            raise ValidationError('La Addenda/Complemento "%s" no esta implementado'%(cfd_addenda))
            return False
        return True



########################################
#
# Quitar en Futuras versiones
#
########################################
class TipoPago(models.Model):
    _name = "cfd_mx.tipopago"

    name = fields.Char("Descripcion", size=128, required=True, default="")

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    aprobacion_ids = fields.One2many("cfd_mx.aprobacion", 'sequence_id', string='Aprobaciones')

class Aprobacion(models.Model):
    _name = 'cfd_mx.aprobacion'

    anoAprobacion = fields.Integer(string="Año de aprobación", required=True)
    noAprobacion = fields.Char(string="No. de aprobación", required=True)
    serie = fields.Char(string="Serie", size=8)
    del_field = fields.Integer(string="Del", required=True, oldname='del')
    al = fields.Integer(string="Al", required=True)
    sequence_id = fields.Many2one("ir.sequence", string="Secuencia", required=True)

class certificate(models.Model):
    _name = 'cfd_mx.certificate'

    serial = fields.Char(string="Número de serie", size=64, required=True)
    cer = fields.Binary(string='Certificado', filters='*.cer,*.certificate,*.cert', required=True)
    key = fields.Binary(string='Llave privada', filters='*.key', required=True)
    key_password = fields.Char('Password llave', size=64, invisible=False, required=True)
    cer_pem = fields.Binary(string='Certificado formato PEM', filters='*.pem,*.cer,*.certificate,*.cert')
    key_pem = fields.Binary(string='Llave formato PEM', filters='*.pem,*.key')
    pfx = fields.Binary(string='Archivo PFX', filters='*.pfx')
    pfx_password = fields.Char(string='Password archivo PFX', size=64, invisible=False)
    start_date = fields.Date(string='Fecha inicio', required=False)
    end_date = fields.Date(string='Fecha expiración', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', 
            required=True, default=lambda self: self.env.user.company_id.id)
    active = fields.Boolean(default=True, help="If the active field is set to False, it will allow you to hide the certificate without removing it.")

########################################
#
# Quitar en Futuras versiones
#
########################################