from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _prepare_line_values(self, line, account_id, date, debit, credit):

        if line.code == 'ARL':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'arl')], limit=1).partner_id.id
        elif line.code == 'CAJACOMPENSACION':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'ccf')], limit=1).partner_id.id
        elif line.code == 'SALUDEMPRESA':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'eps')], limit=1).partner_id.id
        elif line.code == 'PENSIONEMPRESA':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'afp')], limit=1).partner_id.id
        elif line.code == 'CESANTIAS':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'fc')], limit=1).partner_id.id
        elif line.code == 'PROVCESANTIA':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'fc')], limit=1).partner_id.id
        else:
            partner = line.employee_id.partner_id.id

        return {
            'name': line.name,
            'partner_id': partner,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
            'analytic_tag_ids': (4, line.slip_id.contract_id.analytic_account_id.tag_id.id)
        }