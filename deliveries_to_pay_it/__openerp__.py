# -*- encoding: utf-8 -*-
{
	'name': 'Deliveries To Pay IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account', 'account_tables_it', 'account_voucher','account_parameter_it'],
	'version': '1.0',
	'description':"""
	Modulo de entregas a rendir con parametros generales
	""",
	'auto_install': False,
	'demo': [],
	'data':	['deliveries_to_pay_view.xml','account_move_line_view.xml','voucher_payment_receipt_view.xml','account_view.xml'],
	'installable': True
}
