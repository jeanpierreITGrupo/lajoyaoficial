# -*- encoding: utf-8 -*-
{
	'name': 'Vacations Role IT',
	'category': 'hr',
	'author': 'ITGrupo',
	'depends': ['account','hr_nomina_it'],
	'version': '1.0',
	'description':"""
		Módulo que permite asignar vacaciones a empleados y consultarlas por periodo.
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/vacations_wizard.xml','vacations_role.xml'],
	'installable': True
}
