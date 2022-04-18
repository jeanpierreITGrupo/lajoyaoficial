# -*- encoding: utf-8 -*-
{
	'name': 'Account Campos Sunat PLE IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it','account_move_sunat_it'],
	'version': '1.0',
	'description':"""
	Se agregara todos los campos necesraios para los PLEs 								

	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_view.xml','account_invoice_view.xml'],
	'installable': True
}
