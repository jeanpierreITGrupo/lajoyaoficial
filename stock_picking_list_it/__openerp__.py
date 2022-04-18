# -*- encoding: utf-8 -*-
{
	'name': 'Picking List View IT',
	'category': 'Stock',
	'author': 'ITGrupo',
	'depends': ['stock', 'kardex'],
	'version': '1.0',
	'description':"""
		Crea menú que muestra picking en un lista y permite:
			- Búsqueda por: Referencia, partner, fecha, doc. origen, orden de producción
			- Agrupación por : Tipo albarán, tipo operación, partner, control de facturas, estado, orden de producción. 
	""",
	'auto_install': False,
	'demo': [],
	'data':	['stock_picking.xml'],
	'installable': True
}