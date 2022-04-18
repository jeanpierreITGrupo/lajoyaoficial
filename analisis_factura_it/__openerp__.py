# -*- encoding: utf-8 -*-
{
	'name': 'Analisis Factura IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','product','account_state_financial_it','account_means_payment_it','account_parameter_it'],
	'version': '1.0',
	'description':"""
	Este modulo permite concilear o desconciliar los apuntes contables con un determinado partner y comprobante
	""",
	'auto_install': False,
	'demo': [],
	'data':	['analisis_factura_view.xml'],
	'installable': True
}
