# -*- encoding: utf-8 -*-
{
	'name': 'Sale Order Trace IT',
	'category': 'Sales',
	'author': 'ITGrupo',
	'depends': ['sale', 'stock', 'stock_account'],
	'version': '1.0',
	'description':"""
		Módulo que agrega fecha de despacho, recepción y límite para el seguimiento de una venta.
	""",
	'auto_install': False,
	'demo': [],
	'data':	['sale_trace.xml',
			],
	'installable': True
}