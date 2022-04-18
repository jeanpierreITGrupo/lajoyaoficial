# -*- encoding: utf-8 -*-
{
	'name': 'Account Forth Category',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account_move_sunat_it', 'account_contable_book_it'],
	'version': '1.0',
	'description':"""
		Libros de Honorarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_forth_category_view.xml','res_partner_view.xml','wizard/account_forth_category_wizard_view.xml','wizard/prestadores_report_view.xml', 'wizard/fees_report_view.xml'],
	'installable': True
}
