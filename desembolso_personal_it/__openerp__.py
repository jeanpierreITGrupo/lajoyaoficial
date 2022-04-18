# -*- encoding: utf-8 -*-
{
	'name': 'Desembolso Personal IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','product','account_state_financial_it','account_means_payment_it','account_parameter_it'],
	'version': '1.0',
	'description':"""
	Este modulo crea un wizard para gestionar los adelantos y prestamos al personal, directores y socios.
	""",
	'auto_install': False,
	'demo': [],
	'data':	['egreso_trabajador_view.xml'],
	'installable': True
}
