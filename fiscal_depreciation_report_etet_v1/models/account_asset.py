from odoo import fields, models, api
import datetime
import calendar
from dateutil.relativedelta import relativedelta
from math import copysign

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round

class AccountAsset(models.Model):
    _inherit = 'account.asset'
    _description = 'Description'

    valorizado = fields.Boolean(string="Valorizado", help="Si el activo esta valorizado marque la casilla")
    duracion_f = fields.Integer(string='Number of Depreciations', readonly=True, states={'draft': [('readonly', False)], 'model': [('readonly', False)]}, default=5, help="Numero de depreciaciones para el activo informe fiscal ")
    tax_residual_value = fields.Monetary(string="Costo Fiscal")
    non_depreciable_value = fields.Monetary(string="Valor Residual Fiscal")
    method_period_fiscal = fields.Selection([('1', 'Meses'), ('12', 'Años')], string='Number of Months in a Period',
                                     readonly=True, default='12',
                                     states={'draft': [('readonly', False)], 'model': [('readonly', False)]},
                                     help="The amount of time between two depreciations")
    fiscal_depreciation_move_ids = fields.One2many('account.move_fiscal', 'asset_id', string='Lineas de Depreciacion')
    ref_asset = fields.Char(string="Referencia")
    responsable_asset = fields.Many2one('hr.employee', string="Responsable del Activo")
    cargo = fields.Char(string="cargo", compute='_cargo')
    invoice_purchases = fields.Many2one('account.move', string="Facturas de compra")
    invoice_date = fields.Char(string='fecha', compute='_invoice_date')
    invoice_partner = fields.Char(string='proveedor', compute='_invoice_partner')
#    adition_asset_line_ids = fields.One2many('account.adition_asset', 'adition_asset_id', string='Adicion Activos Fijos')
    location_asset_line_ids = fields.Many2one('account.location_asset', string='Ubicacion Activo')
#    value_adition = fields.Integer(compute= '_adition_asset_value')
    old_asset = fields.Boolean(string='Activo Antiguo' ,help="Si el activo es antiguo y tiene amortizaciones anteriores marque la casilla")
    asset_depreciate_value_initial = fields.Integer(string='Saldo Amortizaciones Anteriores' )
#    residual_value_asset_old = fields.Integer(string= 'Valor a Depreciar Activos Antiguos', compute='_residual_value_asset_old')
    purchase_amount_asset = fields.Integer(string='Valor Compra Activo')

    
    @api.onchange('invoice_purchases')
    def _invoice_date(self):
        self.invoice_date = self.invoice_purchases.invoice_date
        self.invoice_partner = self.invoice_purchases.partner_id.name

    @api.onchange('responsable_asset')
    def _cargo(self):
        self.cargo = self.responsable_asset.job_title


    def compute_depreciation_fiscal_board(self):
        self.ensure_one()
        amount_change_ids = self.depreciation_move_ids.filtered(lambda x: x.asset_value_change and not x.reversal_move_id).sorted(key=lambda l: l.date)
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id).sorted(key=lambda l: l.date)
        already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids])
        depreciation_number = self.duracion_f
        if self.prorata:
            depreciation_number += 1
        starting_sequence = 0
        amount_to_depreciate = (self.tax_residual_value - self.non_depreciable_value) + sum([m.amount_total for m in amount_change_ids])
        depreciation_date = self.first_depreciation_date
        # if we already have some previous validated entries, starting date is last entry + method period
        if posted_depreciation_move_ids and posted_depreciation_move_ids[-1].date:
            last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].date)
            if last_depreciation_date > depreciation_date:  # in case we unpause the asset
                depreciation_date = last_depreciation_date + relativedelta(months=+int(self.method_period_fiscal))
        commands = [(2, line_id.id, False) for line_id in self.fiscal_depreciation_move_ids]
        newlines = self._recompute_board(depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids)
        newline_vals_list = []
        for newline_vals in newlines:
            # no need of amount field, as it is computed and we don't want to trigger its inverse function
            del(newline_vals['amount_total'])

            newline_vals_list.append(newline_vals)
        for val in newline_vals_list:
            vals = {
                "ref_fiscal": val['ref'],
                "asset_remaining_value_fiscal": val['asset_remaining_value'],
                "asset_depreciated_value_fiscal": val['asset_depreciated_value'],
                "date_fiscal": val['date'],
                "amount_total": (self.tax_residual_value - self.non_depreciable_value) / self.duracion_f

            }
            move = self.env['account.move_fiscal'].create(vals)
            commands.append((4, move.id))

        return self.write({'fiscal_depreciation_move_ids': commands})

    def _get_disposal_moves(self, invoice_line_ids, disposal_date):
        def get_line(asset, amount, account):
            return (0, 0, {
                'name': asset.name,
                'account_id': account.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id if asset.asset_type == 'sale' else False,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * asset.value_residual or 0.0,
            })

        move_ids = []
        assert len(self) == len(invoice_line_ids)
        for asset, invoice_line_id in zip(self, invoice_line_ids):
            if disposal_date < max(asset.depreciation_move_ids.filtered(
                    lambda x: not x.reversal_move_id and x.state == 'posted').mapped('date') or [fields.Date.today()]):
                if invoice_line_id:
                    raise UserError(
                        'There are depreciation posted after the invoice date (%s).\nPlease revert them or change the date of the invoice.' % disposal_date)
                else:
                    raise UserError('There are depreciation posted in the future, please revert them.')
            account_analytic_id = asset.account_analytic_id
            analytic_tag_ids = asset.analytic_tag_ids
            company_currency = asset.company_id.currency_id
            current_currency = asset.currency_id
            prec = company_currency.decimal_places
            unposted_depreciation_move_ids = asset.depreciation_move_ids.filtered(lambda x: x.state == 'draft')
            if unposted_depreciation_move_ids:
                old_values = {
                    'method_number': asset.method_number,
                }

                # Remove all unposted depr. lines
                commands = [(2, line_id.id, False) for line_id in unposted_depreciation_move_ids]

                # Create a new depr. line with the residual amount and post it
                asset_sequence = len(asset.depreciation_move_ids) - len(unposted_depreciation_move_ids) + 1
                saldo_depreciacion = asset.asset_depreciate_value_initial
                initial_amount = asset.purchase_amount_asset if asset.old_asset == True else asset.original_value
                initial_account = asset.original_move_line_ids.account_id if len(
                    asset.original_move_line_ids.account_id) == 1 else asset.account_asset_id
                depreciated_amount = copysign(sum(asset.depreciation_move_ids.filtered(lambda r: r.state == 'posted').mapped('amount_total')), -initial_amount)
                if asset.old_asset == True:
                    depreciated_amount = depreciated_amount - saldo_depreciacion
                depreciation_account = asset.account_depreciation_id
                invoice_amount = copysign(invoice_line_id.price_subtotal, -initial_amount)
                invoice_account = invoice_line_id.account_id
                difference = -initial_amount - depreciated_amount - invoice_amount
                difference_account = asset.company_id.gain_account_id if difference > 0 else asset.company_id.loss_account_id
                line_datas = [(initial_amount, initial_account), (depreciated_amount, depreciation_account),
                              (invoice_amount, invoice_account), (difference, difference_account)]
                if not invoice_line_id:
                    del line_datas[2]
                vals = {
                    'amount_total': current_currency._convert(asset.value_residual, company_currency, asset.company_id,
                                                              disposal_date),
                    'asset_id': asset.id,
                    'ref': asset.name + ': ' + (_('Disposal') if not invoice_line_id else _('Sale')),
                    'asset_remaining_value': 0,
                    'asset_depreciated_value': max(asset.depreciation_move_ids.filtered(lambda x: x.state == 'posted'),
                                                   key=lambda x: x.date,
                                                   default=self.env['account.move']).asset_depreciated_value,
                    'date': disposal_date,
                    'journal_id': asset.journal_id.id,
                    'line_ids': [get_line(asset, amount, account) for amount, account in line_datas if account],
                }
                commands.append((0, 0, vals))
                asset.write({'depreciation_move_ids': commands, 'method_number': asset_sequence})
                tracked_fields = self.env['account.asset'].fields_get(['method_number'])
                changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
                if changes:
                    asset.message_post(body=_('Asset sold or disposed. Accounting entry awaiting for validation.'),
                                       tracking_value_ids=tracking_value_ids)
                move_ids += self.env['account.move'].search([('asset_id', '=', asset.id), ('state', '=', 'draft')]).ids

        return move_ids


