# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Informe prenomina',
    'version': '1.0',
    'summary': 'summarys',
    'description': "reportes Nomina",
    'website': 'https://www.endtoendt.com',
    'depends': ['account', 'hr_payroll_extended'],
    'category': 'category',
    'author': 'Enrrique Aguiar',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'views/prenomina_report_view.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,

}
