# -*- coding: utf-8 -*-

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class HrLoan(models.Model):
    _inherit = "hr.loan"


    input_id = fields.Many2one('hr.payslip.input.type', string='Input', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    loan_fijo = fields.Boolean('Fijo', default=False, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
        ('done', 'Terminado'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )
    contract_id = fields.Many2one('hr.contract', string='Contract', track_visibility='onchange')
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('bimonthly', 'Bi-monthly'),
    ], string="Frecuencia de pago", default='monthly', track_visibility='onchange', copy=False)
    bimonthly_pay = fields.Selection([
        ('primera', 'Primera'),
        ('segunda', 'Segunda'),
        ('ambas', 'Primera y Segunda'),
    ], string="Quincena de pago", default='primera', track_visibility='onchange', copy=False)     


    def action_done(self):
        self.write({'state': 'done'})

    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.onchange('employee_id')
    def onchange_employee(self):
        for loan in self:
            if loan.employee_id:
                contract = self.env["hr.contract"].search([('employee_id', '=', loan.employee_id.id),('state','=','open')], limit=1)
                if contract:
                    loan.contract_id=contract.id
                else:
                    raise UserError(_('El empleado %s no tiene un contracto.') % (loan.employee_id.name,))


    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            if self.schedule_pay=='monthly':
                for i in range(1, loan.installment + 1):
                    self.env['hr.loan.line'].create({
                        'date': date_start,
                        'amount': amount,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})
                    date_start = date_start + relativedelta(months=1)
            else:
                for i in range(1, loan.installment + 1):
                    self.env['hr.loan.line'].create({
                        'date': date_start,
                        'amount': amount,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})
                    date_start = date_start + relativedelta(days=15)                
            loan._compute_loan_amount()
        return True
    