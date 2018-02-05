# coding: utf-8
# 
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, api, _

"""
      'IEPS Ventas':         account_obj.search([('code', '=', '208.02.xx')]), # 209.02.xx IEPS trasladado no cobrado/ 208.02.xx IEPS trasladado cobrado
      'IEPS Exportaciones':  account_obj.search([('code', '=', 'xxx.xx.xx')]), # ??
      'IEPS Compras':        account_obj.search([('code', '=', '118.03.xx')]), # 119.03.xx IEPS pendiente de pago/ 118.03.xx IEPS acreditable pagado
      'IEPS Importaciones':  account_obj.search([('code', '=', '118.04.xx')]), # 119.04.xx IEPS pendiente de pago en importación/ 118.04.xx IEPS pagado en importación
"""

class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    @api.multi
    def _load_template(
            self, company, code_digits=None, transfer_account_id=None,
            account_ref=None, taxes_ref=None):
        """
        Set the 'use_cash_basis' and 'cash_basis_account' fields on account.account.
        """
        self.ensure_one()
        accounts, taxes = super(AccountChartTemplate, self)._load_template(
            company, code_digits=code_digits,
            transfer_account_id=transfer_account_id, account_ref=account_ref,
            taxes_ref=taxes_ref)
        if not self == self.env.ref('l10n_mx_sat_openbias.mx_coa_sat'):
            return accounts, taxes
        account_tax_obj = self.env['account.tax']
        account_obj = self.env['account.account']
        taxes_acc = {
                #209.01.01 IVA trasladado no cobrado / 208.01.01 IVA trasladado cobrado
                'IVA(0%) VENTAS': account_obj.search([('code', '=', '208.01.01'),('company_id', '=', company.id)]),  
                #209.01.01 IVA trasladado no cobrado / 208.01.01 IVA trasladado cobrado
                'IVA Exento': account_obj.search([('code', '=', '208.01.01'),('company_id', '=', company.id)]),  
                #209.01.01 IVA trasladado no cobrado / 208.01.01 IVA trasladado cobrado
                'IVA(16%) VENTAS': account_obj.search([('code', '=', '208.01.01'),('company_id', '=', company.id)]),  
                #119.01.01 IVA pendiente de pago     / 118.01.01 IVA acreditable pagado
                'IVA(0%) COMPRAS': account_obj.search([('code', '=', '118.01.01'),('company_id', '=', company.id)]),  
                #119.01.01 IVA pendiente de pago     / 118.01.01 IVA acreditable pagado
                'IVA(16%) COMPRAS': account_obj.search([('code', '=', '118.01.01'),('company_id', '=', company.id)]),  
                #119.02.01 IVA de importación pendiente de pago / 118.02.01 IVA acreditable de importación pagado
                'IVA Exento en Importaciones': account_obj.search([('code', '=', '118.02.01'),('company_id', '=', company.id)]),  
                #119.02.01 IVA de importación pendiente de pago / 118.02.01 IVA acreditable de importación pagado
                'IVA 16% en compras usado en pedimentos': account_obj.search([('code', '=', '118.02.01'),('company_id', '=', company.id)]),
            }  
        for tax in self.tax_template_ids:
            if tax.description not in taxes_acc:
                continue
            account_tax_obj.browse(taxes.get(tax.id)).write({
                'use_cash_basis': True,
                'cash_basis_account': taxes_acc.get(tax.description).id,
            })
        return accounts, taxes

    @api.model
    def generate_journals(self, acc_template_ref, company, journals_dict=None):
        """Set the tax_cash_basis_journal_id on the company"""
        res = super(AccountChartTemplate, self).generate_journals(
            acc_template_ref, company, journals_dict=journals_dict)
        if not self == self.env.ref('l10n_mx_sat_openbias.mx_coa_sat'):
            return res
        journal_basis = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('code', '=', 'TRIVA')], limit=1)
        company.write({'tax_cash_basis_journal_id': journal_basis.id})
        return res

    @api.multi
    def _prepare_all_journals(self, acc_template_ref, company, journals_dict=None):
        """Create the tax_cash_basis_journal_id"""
        res = super(AccountChartTemplate, self)._prepare_all_journals(
            acc_template_ref, company, journals_dict=journals_dict)
        if not self == self.env.ref('l10n_mx_sat_openbias.mx_coa_sat'):
            return res
        res.append({
            'type': 'general',
            'name': _('Efectivamente pagado'),
            'code': 'TRIVA',
            'company_id': company.id,
            'show_on_dashboard': False,
        })
        account = self.env.ref('l10n_mx_sat_openbias.account_102_01_01')   
        res.append({
            'type': 'bank',
            'name': _('Banco'),
            'code': 'BNKT',
            'company_id': company.id,
            'default_credit_account_id': account.id,
            'default_debit_account_id': account.id,
            'show_on_dashboard': True,
        })
        return res


    def _get_account_vals(self, company, account_template, code_acc, tax_template_ref):
        """ se agregan 4 campos agregados en accoun.account.template de coa"""
        val = super(AccountChartTemplate, self)._get_account_vals(company, account_template, code_acc, tax_template_ref)
        if not self == self.env.ref('l10n_mx_sat_openbias.mx_coa_sat'):
            return val
        if account_template.codigo_agrupador and account_template.codigo_agrupador.id:
            val['codigo_agrupador_id'] = account_template.codigo_agrupador and account_template.codigo_agrupador.id
        if account_template.naturaleza and account_template.naturaleza.id:
            val['naturaleza_id'] = account_template.naturaleza and account_template.naturaleza.id
        if account_template.parent_id and account_template.parent_id.id:
            val['parent_id'] = account_template.parent_id and account_template.parent_id.id
        val['type'] = account_template.type
        return val

