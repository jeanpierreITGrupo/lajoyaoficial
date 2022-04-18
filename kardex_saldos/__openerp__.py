# -*- encoding: utf-8 -*-
{
	'name': 'kardex Saldos',
	'category': 'purchase',
	'author': 'ITGrupo',
	'depends': ['stock'],
	'version': '1.0',
	'description':"""Muestra los saldos de los productos para unos almacenes a una fecha determinada""",
	'auto_install': False,
	'demo': [],
	'data':['security/kardex_saldos_security.xml',
			'security/ir.model.access.csv',
			'kardex_saldos_view.xml',
		   	'wizard/get_kardex_saldos_view.xml'],
	'installable': True
}
