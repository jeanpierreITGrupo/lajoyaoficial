# -*- encoding: utf-8 -*-
{
	'name': 'Sale Cost Journal IT',
	'category': 'manufacture',
	'author': 'ITGrupo',
	'depends': ['kardex'],
	'version': '1.0',
	'description':"""
		Módulo que permite crear asientos de costo de producción. 
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/sale_cost_wizard.xml',
			'sale_cost_journal.xml'],
	'installable': True
}