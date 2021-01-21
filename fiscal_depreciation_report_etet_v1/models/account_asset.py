from odoo import fields, models, api
import datetime

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
    adition_asset_line_ids = fields.One2many('account.adition_asset', 'adition_asset_id', string='Adicion Activos Fijos')
    location_asset_line_ids = fields.Many2one('account.location_asset', string='Ubicacion Activo')
    value_adition = fields.Integer(compute= '_adition_asset_value')

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


#        new_moves = self.env['account.move_fiscal'].create(newline_vals_list)
#        for move in new_moves:
#           commands.append((4, move.id))
        return self.write({'fiscal_depreciation_move_ids': commands})



