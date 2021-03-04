from odoo import fields, models, api
from odoo.exceptions import ValidationError

class hr_deductions_rt (models.Model):
    _name = 'hr_deductions_rt'
    _description = 'Deducciones de retención en la fuente metodo 1'
    _rec_name = 'concept'

    concept = fields.Char('Concepto')
    amount = fields.Integer(default=1, string="monto")

    _sql_constraints = [
        ('concept_id_uniq', 'unique(concept)', "Ya existe este concepto!"),
    ]









