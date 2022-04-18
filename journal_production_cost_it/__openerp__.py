# -*- encoding: utf-8 -*-
{
	'name': 'Production Cost Journal IT',
	'category': 'manufacture',
	'author': 'ITGrupo',
	'depends': ['kardex'],
	'version': '1.0',
	'description':"""
		Módulo que permite crear asientos de costo de producción. 
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/production_cost_wizard.xml',
			'production_cost_journal.xml'],
	'installable': True
}