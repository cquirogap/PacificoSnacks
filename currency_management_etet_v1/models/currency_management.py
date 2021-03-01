# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import time
from datetime import datetime, timedelta, date
import xlwt
import base64
# from cStringIO import StringIO
from io import StringIO
from io import BytesIO
import xlsxwriter
import types
import logging

_logger = logging.getLogger(__name__)


class DivisasReport(models.TransientModel):
    _name = 'divisas.report'
    _description = 'Reporte Divisas'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    fecha_inicial = fields.Date(string='Fecha de Inicial')
    fecha_final = fields.Date(string='Fecha de Final')
    estado = fields.Boolean(string='pago')
    date_creation = fields.Date('Created Date', required=True, default=fields.Date.today())
    facturas = fields.Many2many('account.move', string='facturas', required=True)
    pagos = fields.Many2many('account.payment', string='pagos')

#    exist_facturas = fields.Boolean(string='facturas existentes', compute='get_data_facturas')

    @api.onchange('facturas')
    def get_data_facturas(self):
        if self.facturas:
            self.exist_facturas = True
        else:
            self.exist_facturas = False

    @api.onchange('fecha_inicial')
    def onchange_facturas_pag(self):
        for rec in self:
            return {'domain': {'facturas': [('name', 'like', 'FE'), ('partner_id.category_id.id', '=', '101')]}}

    def do_report(self):

        _logger.error("INICIA LA FUNCIÓN GENERAR EL REPORTE ")
        self.make_file()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=divisas.report&field=data&id=%s&filename=%s' % (
                self.id, self.data_name),
            'target': 'new',
            'nodestroy': False,
        }

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")

        pagos = self.env['account.payment'].search([("currency_id", "!=", 8), '&', ("payment_date", ">=", self.fecha_inicial), ("payment_date", "<=", self.fecha_final)])
        date_creation = fields.Date.today()

        if not pagos:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        ws.set_column('A:A', 15)
        ws.set_column('B:B', 65)
        ws.set_column('C:Z', 18)
        # formatos
        title_head = wb.add_format({
            'bold': 1,
            'border': 1,
            'align': 'rigth',
            'fg_color': '#33CCCC',
            'valign': 'vcenter',

        })
        title_head.set_font_name('Arial')
        title_head.set_font_size(10)
        title_head.set_font_color('black')
        format_date = wb.add_format({'num_format': 'mm/dd/yyyy'})
        format_number = wb.add_format({'num_format': '#,##0.00'})

        ws.write(0, 1, 'PACIFICO SNACKS', title_head)
        ws.write(1, 3, date_creation, format_date)
        ws.write(1, 0, 'Reporte Divisas', title_head)
        ws.write(1, 2, 'Fecha:')


        ws.write(2, 0, 'FECHA DE FACTURA', title_head)
        ws.write(2, 1, 'TERCERO', title_head)
        ws.write(2, 2, 'N° DE FV', title_head)
        ws.write(2, 3, 'TRM EN VENTA', title_head)
        ws.write(2, 4, 'TOTAL USD', title_head)
        ws.write(2, 5, 'TOTAL FISCAL', title_head)
        ws.write(2, 6, 'TRM', title_head)
        ws.write(2, 7, 'TOTAL CONTABLE', title_head)
        ws.write(2, 8, 'DIFERENCIA', title_head)
        ws.write(2, 9, 'FECHA DE PAGO', title_head)

        fila = 3
        for pay in pagos:
            if pay.invoice_ids:
                for fv in pay.invoice_ids:
                    valor_trm = fv.trm
                    valor_factura = fv.amount_total
                    valor_total_fiscal = valor_factura * valor_trm
                    trm_2 = pay.trm
                    valor_total_contable = valor_factura * trm_2

                    valor_diferencia = valor_total_fiscal - valor_total_contable
                    ws.write(fila, 0, '') if not fv.name else ws.write(fila, 0, fv.invoice_date, format_date)
                    ws.write(fila, 1, '') if not fv.name else ws.write(fila, 1, fv.invoice_partner_display_name)
                    ws.write(fila, 2, '') if not fv.name else ws.write(fila, 2, fv.name)
                    ws.write(fila, 3, '') if not fv.name else ws.write(fila, 3, valor_trm, format_number)
                    ws.write(fila, 4, '') if not fv.name else ws.write(fila, 4, valor_factura, format_number)

                    ws.write(fila, 5, '') if not fv.name else ws.write(fila, 5, valor_total_fiscal, format_number)
                    ws.write(fila, 6, '') if not fv.name else ws.write(fila, 6, trm_2, format_number)
                    ws.write(fila, 7, '') if not fv.name else ws.write(fila, 7, valor_total_contable, format_number)
                    ws.write(fila, 8, '') if not fv.name else ws.write(fila, 8, valor_diferencia, format_number)
                    ws.write(fila, 9, '') if not fv.name else ws.write(fila, 9, pay.payment_date, format_date)
                fila += 1


        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'REPORTE DIVISAS' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#
