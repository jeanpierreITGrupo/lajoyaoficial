# -*- encoding: utf-8 -*-
{
	'name': 'Account Move Analytic IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_move_sunat_it','account_analytic_plans','purchase_analytic_plans','sale_analytic_plans'],
	'version': '1.0',
	'description':"""
	Mostrar las lineas analyticas de los asientos ocntables
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_view.xml'],
	'installable': True
}
