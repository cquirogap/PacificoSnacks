# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
           
class HrExtras(models.Model):
    _name = "hr.extras"
    _inherit = ['mail.thread']
    _description = "Hr Extras"
    _order = "name desc, id desc"


    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('cancel','Cancelled')], 
                                    string='State', track_visibility='onchange', default='draft')
    name = fields.Char('Name', readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract', track_visibility='onchange')
    date = fields.Date('Date', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float(string='Quantity', default=0.0, readonly=True, states={'draft': [('readonly', False)]})
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', readonly=True)
    input_id = fields.Many2one('hr.payslip.input.type', string='Input', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})


    _sql_constraints = [
        ('employee_date_input_uniq', 'unique(date, input_id, employee_id)',
            'Input must be unique per Employee!'),
    ]
    

    def name_get(self):
        return [(hour.id, '%s - %s' % (hour.employee_id.name, hour.date)) for hour in self]


    @api.onchange('employee_id','date')
    def onchange_employee(self):
        for hour in self:
            if hour.employee_id:
                contract = self.env["hr.contract"].search([('employee_id', '=', hour.employee_id.id),('state','=','open')], limit=1)
                if contract:
                    hour.contract_id=contract.id
                    hour.name = hour.employee_id.name + ' - ' + str(hour.date)
                else:
                    raise UserError(_('El empleado %s no tiene un contracto.') % (hour.employee_id.name,))
                    hour.name = hour.employee_id.name + ' - ' + str(hour.date)


    def action_approve_input(self):
        self.write({'state': 'approved'})



    def action_cancelled_approved_input(self):
        self.write({'state': 'cancel'})



    def action_draft_input(self):
        self.write({'state': 'draft'})



    def action_cancelled_input(self):
        if not self.payslip_id:
            self.write({'state': 'cancel'})