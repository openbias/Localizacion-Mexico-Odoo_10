# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo
from odoo import api, fields, models, _

ADDRESS_FIELDS2 = ('street', 'street2', 'colonia_id', 'zip', 'city', 'ciudad_id', 'municipio_id', 'state_id', 'country_id', 'noExterior', 'noInterior')

class partner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner']

    extension_phone = fields.Char('Extension Phone', help='Internal phone number.')
    short_number = fields.Char('Short Number', help='Short phone number.')

    xml_cfdi_sinacento = fields.Boolean(string='XML CFDI sin acentos', default=False)
    noInterior = fields.Char(string='No. interior', size=64)
    noExterior = fields.Char(string='No. exterior', size=64)
    identidad_fiscal = fields.Char(string='Registro de Identidad Fiscal', size=40, help='Es requerido cuando se incluya el complemento de comercio exterior')
    regimen_id = fields.Many2one('cfd_mx.regimen', string="Regimen Fiscal")
    formapago_id = fields.Many2one("cfd_mx.formapago", string="Forma de Pago")
    metodopago_id = fields.Many2one('cfd_mx.metodopago', string=u'Metodo de Pago')

    usocfdi_id = fields.Many2one('cfd_mx.usocfdi', string="Uso de Comprobante CFDI")
    es_extranjero = fields.Boolean(string='Es Extranjero?', default=False)
    es_personafisica = fields.Boolean(string="Es Persona Fisica?")
    curp = fields.Char(string="CURP", help="Llenar en caso de que el empleador sea una persona física")
    
    # Quitar en futuras Versiones
    metodo_pago = fields.Many2one("cfd_mx.formapago", string="Metodo de pago")
    fiscal_id = fields.Char(string='Fiscal ID', size=32, help="Tax identifier for Foreign partners.")
    supplier_type = fields.Selection([
        ('04','Proveedor Nacional'),
        ('05','Proveedor Extranjero'),
        ('15','Proveedor Global')], 
        string='Supplier Type', default='04', 
        help="Define the type of supplier, this field is used to get the DIOT report.")
    operation_type = fields.Selection([
        ('03','Prestación de Servicios Profesionales'),
        ('06','Arrendamiento de Inmuebles'),
        ('85','Otros')], 
        string='Operation Type', default='85', 
        help="Define the operation type, when partner type is 05 the only valid selections are 03 and 85, this field is used to get the DIOT report.")

    cfdi_addenda = fields.Many2one('ir.ui.view',
        string='Addenda',
        help='A view representing the addenda',
        domain=[('is_addenda', '=', True)])

    @api.model
    def _address_fields_2(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        return list(ADDRESS_FIELDS2)

    @api.multi
    def _display_address(self, without_company=False):
        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''

        # get the information that will be injected into the display format
        # get the address format
        address_format = self.country_id.address_format or \
              "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
            'company_name': self.commercial_company_name or '',
        }
        if getattr(self, 'noExterior', None):
            args['noExterior'] = self.noExterior or ''
        if getattr(self, 'noInterior', None):
            args['noInterior'] = self.noInterior or ''
        # if getattr(self, 'colonia_name', None):
        #     args['colonia_name'] = self.colonia_id and self.colonia_id.name or ''
        if getattr(self, 'ciudad_name', None):
            args['ciudad_name'] = self.ciudad_id and self.ciudad_id.name or ''
        if getattr(self, 'municipio_name', None):
            args['municipio_name'] = self.municipio_id and self.municipio_id.name or ''

        for field in self._address_fields_2():
            try:
                args[field] = getattr(self, field) or ''
            except:
                pass

        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: