# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta


class AccountlocationAsset(models.Model):
    _name = 'account.location_asset'
    _rec_name = 'codigo'
#    location_asset_id = fields.Many2one('account.asset', string='Tipo de activo')

    codigo = fields.Char(string='codigo')
    nombre = fields.Char(string='nombre')
    pais = fields.Many2one('res.country', string='Pais')
    departamento = fields.Many2one('res.country.state', string='Departamento')
    ciudad = fields.Many2one('res.city', string='Ciudad')
    direccion = fields.Char(string='Direccion')








