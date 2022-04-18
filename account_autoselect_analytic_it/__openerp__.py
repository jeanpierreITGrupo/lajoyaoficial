# -*- encoding: utf-8 -*-
{
	'name': 'Account Auto Select Analytic IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','purchase','account_voucher','product','account_tables_it','account_type_doc_it','product_analytic_account_it'],
	'version': '1.0',
	'description':"""
	
	Agregar analytico distribucion en product y account account									
	Campos:
	-analytic_account_id
	-analytic_distribution_id 
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_invoice_view.xml'],
	'installable': True
}
