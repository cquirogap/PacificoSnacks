# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Certificaciones iva, retefuente e ica',
    'version': '1.0',
    'summary': 'summary',
    'description': "Certificaciones iva, retefuente e ica",
    'website': 'https://www.endtoendt.com',
    'depends': ['account', 'l10n_co_reports'],
    'category': 'category',
    'author': 'Enrrique Aguiar',
    'sequence': 13,
    'demo': [
        
    ],
    'data': [

        'report/certification_report_inherit.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
