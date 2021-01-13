# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta


class AccountAditionAsset(models.Model):
    _name = 'account.adition_asset'

    adition_asset_id = fields.Many2one('account.asset')

    evaluador = fields.Boolean(string="Avaluo", help="Si el activo esta valorizado marque la casilla")
    nombre_adicion = fields.Char(string="Nombre Articulo")
    duracion_adicional = fields.Integer(string='Number of Depreciations')
    valor_adicion = fields.Integer(string="valor")






