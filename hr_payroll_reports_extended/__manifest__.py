# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Report Payroll',
    'version': '1.0',
    'summary': 'Report Payroll',
    'description': "",
    'website': 'https://www.endtoendt.com',
    'depends': ['hr_payroll',],
    'category': 'Operations/Inventory',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'wizard/hr_payroll_report_wizard_view.xml',
        'views/hr_payslip_run_view.xml',
        'security/ir.model.access.csv',

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
