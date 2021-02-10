# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta


class AccountAssetSell(models.TransientModel):
    _inherit = 'account.asset.sell'

    @api.depends('asset_id', 'invoice_id', 'invoice_line_id')
    def _compute_gain_or_loss(self):
        for record in self:
            line = record.invoice_line_id or len(
                record.invoice_id.invoice_line_ids) == 1 and record.invoice_id.invoice_line_ids or self.env[
                       'account.move.line']
            if record.asset_id.purchase_amount_asset < abs(line.balance):
                record.gain_or_loss = 'gain'
            elif record.asset_id.purchase_amount_asset > abs(line.balance):
                record.gain_or_loss = 'loss'
            else:
                record.gain_or_loss = 'no'

