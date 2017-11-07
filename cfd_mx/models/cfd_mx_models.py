# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import csv
import os
import inspect

import logging
_logger = logging.getLogger(__name__)

class AltaCatalogosCFDI(models.TransientModel):
    _name = 'cf.mx.alta.catalogos.wizard'
    _description = 'Alta Catalogos CFDI'

    def get_external_id(self, Data, model, state_id, Obj, obj_code, row):
        obj_id = Obj.search([('clave_sat', '=', obj_code), ('state_id', '=', state_id.id )])
        datas = Data.search([('model', '=', model), ('res_id', '=', obj_id.id), ('module', '=', '__export__')])
        for data in datas:
            return '%s.%s'%(data.module, data.name)
        return None

    def get_states_ids(self):
        dict_states = {}
        Data = self.env['ir.model.data']
        Country = self.env.ref('base.mx')
        States = self.env['res.country.state'].search([('country_id', '=', Country.id)])
        for state in States :
            datas = Data.search([('model', '=', 'res.country.state'), ('res_id', '=', state.id), ('module', '=', 'base')])
            for data in datas:
                dict_states[state.code] = '%s.%s'%(data.module, data.name)
        return dict_states

    def get_csv_datas(self, model):
        fname = '/../data/%s.csv' % model
        current_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))        
        path =  current_path+fname
        ifile  = open(path)
        reader = csv.reader(ifile, delimiter=',', quotechar='"')
        return reader

    def action_load_municipio_ciudad(self, model):
        dict_states = self.get_states_ids()
        reader = self.get_csv_datas(model)
        header = []
        body = []
        model_obj = self.env[model]
        for indx, row in enumerate(reader):
            if indx == 0:
                header = row
            else:
                if row[2] in dict_states.keys():
                    row[2] = dict_states.get(row[2])
                body.append(row)
        model_obj.with_context(noupdate=True).load(header, body)
        cr = self._cr
        cr.commit()
        return True

    def action_load_cp(self, model,reader):
        dict_states = self.get_states_ids()
        Data = self.env['ir.model.data']
        Municipio = self.env['res.country.state.municipio']
        Ciudad = self.env['res.country.state.ciudad']

        header = []
        body = []
        model_obj = self.env[model]
        for indx, row in enumerate(reader):
            if indx == 0:
                header = row
            else:
                state_id = self.env.ref(dict_states.get(row[2]))
                row[2] = dict_states.get(row[2])
                if row[3] and row[4]:
                    municipio_id = self.get_external_id(Data, 'res.country.state.municipio', state_id, Municipio, row[3], row)
                    ciudad_id = self.get_external_id(Data, 'res.country.state.ciudad', state_id, Ciudad, row[4], row)
                    row[3] = municipio_id
                    row[4] = ciudad_id
                else:
                    row[3] = None
                    row[4] = None
                body.append(row)
        model_obj.with_context(noupdate=True).load(header, body)
        cr = self._cr
        cr.commit()
        return True

    def action_res_country_state_municipio(self, model):
        self.action_load_municipio_ciudad(model)
        return True

    def action_res_country_state_ciudad(self, model):
        self.action_load_municipio_ciudad(model)
        return True

    def action_res_country_state_cp_1(self, model_1):
        model = model_1.replace('cp_1', 'cp')
        reader = self.get_csv_datas(model_1)
        self.action_load_cp(model,reader)
        return True

    def action_res_country_state_cp_2(self, model_1):
        model = model_1.replace('cp_2', 'cp')
        reader = self.get_csv_datas(model_1)
        self.action_load_cp(model,reader)
        return True

    def action_res_country_state_cp_3(self, model_1):
        model = model_1.replace('cp_3', 'cp')
        reader = self.get_csv_datas(model_1)
        self.action_load_cp(model,reader)
        return True

    def action_res_country_state_cp_4(self, model_1):
        model = model_1.replace('cp_4', 'cp')
        reader = self.get_csv_datas(model_1)
        self.action_load_cp(model,reader)
        return True

    def action_load_data_path(self, model):
        reader = self.get_csv_datas(model)
        header = []
        body = []
        model_obj = self.env[model]
        for indx, row in enumerate(reader):
            if indx == 0:
                header = row
            else:
                body.append(row)
        r = model_obj.with_context(noupdate=True).load(header, body)
        cr = self._cr
        cr.commit()
        return True

    @api.multi
    def action_alta_catalogos(self):
        _logger.info(' Inicia Alta Catalogos')
        models = [
            # 'res.bank',
            # 'cfd_mx.formapago',
            # 'cfd_mx.metodopago',
            # 'cfd_mx.regimen',
            # 'cfd_mx.usocfdi',
            # 'cfd_mx.aduana',
            # 'res.country',
            'res.country.state.municipio',
            'res.country.state.ciudad',
            'cfd_mx.unidadesmedida',
            'cfd_mx.prodserv',
            'res.country.state.cp_1',
            'res.country.state.cp_2',
            'res.country.state.cp_3',
            'res.country.state.cp_4'
        ]
        for model in models:
            model_name = model.replace('.', '_')
            _logger.info(' Model: -- %s'%model_name )
            if hasattr(self, 'action_%s' % model_name):
                getattr(self, 'action_%s' % model_name)(model)
            else:
                self.action_load_data_path(model)
        _logger.info(' Fin Alta Catalogos')
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

class ClaveProdServ(models.Model):
    _name = 'cfd_mx.prodserv'
    _description = 'Clave del Producto o Servicio'

    name = fields.Char("Descripcion", size=264, required=True, default="")
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")

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

    name = fields.Char("Nombre", size=264, required=True, default="")
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    descripcion = fields.Char("Descripcion", required=False, default="")
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

class FormaPago(models.Model):
    _name = 'cfd_mx.formapago'

    name = fields.Char(string="Descripcion", size=64, required=True, default="")
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")
    banco = fields.Boolean(string="Banco", help="Activar este checkbox para que pregunte número de cuenta")
    no_operacion = fields.Boolean(string="Num. Operacion", default=False)
    rfc_ordenante = fields.Boolean(string="RFC Ordenante", default=False)
    cuenta_ordenante = fields.Boolean(string="Cuenta Ordenante", default=False)
    patron_ordenante = fields.Char(string="Patron Ordenante", default='')
    rfc_beneficiario = fields.Boolean(string="RFC Beneficiario", default=False)
    cuenta_beneficiario = fields.Boolean(string="Cuenta Beneficiario", default=False)
    patron_beneficiario = fields.Char(string="Patron Beneficiario", default='')
    tipo_cadena = fields.Boolean(string="Tipo Cadena", default=False)
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

class Aduana(models.Model):
    _name = "cfd_mx.aduana"

    name = fields.Char("Regimen Fiscal", size=128)
    clave = fields.Char(string="Clave", help="Clave del Catálogo del SAT")

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