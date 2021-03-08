# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

from datetime import date, datetime, time
from collections import defaultdict
from odoo import api, fields, models
from odoo.tools import date_utils

from datetime import datetime
from datetime import date

import pytz

import logging

_logger = logging.getLogger(__name__)
           
class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = "hr.contract"
    _description = "Employee Contract"

    vacation_initial = fields.Float(string="Vacaciones iniciales Disfrutadas", default=0)
    accumulated_vacation = fields.Float(string="Vacaciones Acumuladas", compute='get_accumulated_vacation' )
    vacation_used = fields.Float(string="Vacaciones Disfrutadas", compute='get_vacation_used')
    vacations_available = fields.Float(string="Vacaciones Disponibles", compute='get_vacations_available')
    vacations_history = fields.Many2many('hr.leave' ,string="Historial", compute='get_history')

    retention_method = fields.Selection(string='Método de retención en la fuente', selection=[('NA', 'No aplica'),('M1', 'Metodo 1')], default='NA', required=True )

    def get_accumulated_vacation(self):
        date_from = datetime.combine(self.date_start, datetime.min.time())
        if self.date_end != False and self.date_end <= date.today():
            date_to = datetime.combine(self.date_end, datetime.max.time())
        else:
            date_to = datetime.combine(date.today(), datetime.max.time())
        time_worked = self.env['hr.leave']._get_number_of_days(date_from, date_to, self.employee_id.id)['days']
        if float(time_worked) >= 30:
            accumulated_vacation = (time_worked/30) * 1.25
        else:
            accumulated_vacation = 0
        self.accumulated_vacation = accumulated_vacation

    def get_vacation_used(self):
        # El ('holiday_status_id', '=', 6) corresponde al tipo de ausencia de vacaciones, en caso de modificar el registro se debe cambiar el numero a evaluar
        vacations = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id), ('holiday_status_id', '=', 6), ('state', '=', 'validate')])
        vacation_used = 0
        for vacation in vacations:
            vacation_used = vacation_used + vacation.number_of_days

        self.vacation_used = vacation_used + self.vacation_initial

    def get_vacations_available(self):
        self.vacations_available = int(self.accumulated_vacation) - self.vacation_used

    def get_history(self):
        # El ('holiday_status_id', '=', 6) corresponde al tipo de ausencia de vacaciones, en caso de modificar el registro se debe cambiar el numero a evaluar
        self.vacations_history = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id), ('holiday_status_id', '=', 6), ('state', '=', 'validate')])

    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by
                 hierachy (parent=False first, then first level children and
                 so on) and without duplicata
        """
        structures = self.mapped("struct_id")
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def _get_exceed_hours(self, date_from, date_to):

        generated_date_max = min(fields.Date.to_date(date_to), date_utils.end_of(fields.Date.today(), 'month'))
        self._generate_work_entries(date_from, generated_date_max)
        date_from = datetime.combine(date_from, datetime.min.time())
        date_to = datetime.combine(date_to, datetime.max.time())
        exceed_work_data = defaultdict(int)

        work_entries = self.env['hr.work.entry'].search(
            [
                '&', '&',
                ('state', 'in', ['validated', 'draft']),
                ('contract_id', 'in', self.ids),
                '|', '|', '&', '&',
                ('date_start', '>=', date_from),
                ('date_start', '<', date_to),
                ('date_stop', '>', date_to),
                '&', '&',
                ('date_start', '<', date_from),
                ('date_stop', '<=', date_to),
                ('date_stop', '>', date_from),
                '&',
                ('date_start', '<', date_from),
                ('date_stop', '>', date_to),
            ]
        )

        for work_entry in work_entries:
            date_start = work_entry.date_start
            date_stop = work_entry.date_stop
            if work_entry.work_entry_type_id.is_leave:
                contract = work_entry.contract_id
                calendar = contract.resource_calendar_id
                employee = contract.employee_id
                contract_data = employee._get_work_days_data_batch(
                    date_start, date_stop, compute_leaves=False, calendar=calendar
                )[employee.id]

                exceed_work_data[work_entry.work_entry_type_id.id] += contract_data.get('hours', 0)
            else:
                dt = date_stop - date_start
                exceed_work_data[work_entry.work_entry_type_id.id] += dt.days * 24 + dt.seconds / 3600  # Number of hours
        return exceed_work_data