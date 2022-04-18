# -*- encoding: utf-8 -*-
{
	'name': 'Account Sale Register IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account_move_sunat_it', 'account_contable_book_it'],
	'version': '1.0',
	'description':"""
	Registro de Ventas
	""",
	'auto_install': False,
	'demo': [],
    'qweb' : [
        "static/src/xml/account_move_line_quickadd.xml",
    ],
	'data':	['account_sale_register_view.xml','wizard/account_sale_register_report_wizard_view.xml'],
	'installable': True
}
