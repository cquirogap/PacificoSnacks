from odoo import fields, models, api
import re
from datetime import datetime

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _

class CertificationReportInheritFuente(models.AbstractModel):
    _description = 'Colombian Fuente certification report'
    _inherit = 'l10n_co_reports.certification_report.fuente'


    def _get_report_name(self):
        return u'Retención por Terceros'

    def _get_columns_name(self, options):
        return [
            {'name': u'Nombre'},
            {'name': u'Concepto de retención'},
            {'name': u'Monto del Pago Sujeto Retención', 'class': 'number'},
            {'name': u'Retenido Consignado', 'class': 'number'},
            {'name': u'Rorcentaje', 'class': 'number'},
        ]

    def _get_values_for_columns(self, values):
        if values['tax_base_amount'] == 0:
            balance_p = 0
        else:
            balance_p = round((values['balance'] * 100) / (values['tax_base_amount']), 2)
        get_values = [{'name': values['name'], 'field_name': 'name'},
                      {'name': self.format_value(values['tax_base_amount']), 'field_name': 'tax_base_amount'},
                      {'name': self.format_value(values['balance']), 'field_name': 'balance'},
                      {'name': "{}%".format(balance_p), 'field_name': 'porcentaje'}]

        return get_values

class ReportCertificationReportInheritIca(models.AbstractModel):
    _inherit = 'l10n_co_reports.certification_report.ica'
    _description = 'Colombian ICA certification report'

    def _get_report_name(self):
        return u'Retención en ICA'

    def _get_columns_name(self, options):
        return [
            {'name': 'Nombre'},
            {'name': 'Bimestre'},
            {'name': u'Monto del pago sujeto a retención', 'class': 'number'},
            {'name': 'Retenido y consignado', 'class': 'number'},
            {'name': 'porcentaje'},
        ]

    def _get_values_for_columns(self, values):
        if values['tax_base_amount'] == 0:
            balance_p = 0
        else:
            balance_p = round((values['balance'] * 100) / (values['tax_base_amount']), 2)
        get_values = [{'name': values['name'], 'field_name': 'name'},
                      {'name': self.format_value(values['tax_base_amount']), 'field_name': 'tax_base_amount'},
                      {'name': self.format_value(values['balance']), 'field_name': 'balance'},
                      {'name': "{}%".format(balance_p), 'field_name': 'porcentaje'}]

        return get_values