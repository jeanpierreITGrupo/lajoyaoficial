# -*- encoding: utf-8 -*-
{
	'name': 'Account Sheet Work Compare IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it','account_moorage_analytic_it','account_sheet_work'],
	'version': '1.0',
	'description':"""
	HOJA DE TRABAJO	
	COMPARATIVO 
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_sheet_work_view.xml','wizard/account_sheet_work_wizard_view.xml'],
	'installable': True
}
