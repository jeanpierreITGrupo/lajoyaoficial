# -*- encoding: utf-8 -*-
{
	'name'    : 'Disponibilidad en Stock IT',
	'version' : '1.0',
	'author'  : 'ITGrupo',
	'website' : '',
	'category': 'stock',
	'depends' : ['stock', 'kardex'],

	'description': """
		Comprueba la disponibilidad de los productos en un stock picking dependiendo de la ubicación.
	""",

	'demo': [],
	'data': [
		'security/almacen_forzar_security.xml',
		'stock_view.xml',
	],

	'auto_install': False,
	'installable' : True
}

