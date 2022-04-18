# -*- encoding: utf-8 -*-
{
	'name': 'Calculo de retenciones de 5ta categoria',
	'category': 'hr',
	'author': 'ITGrupo',
	'depends': ['hr_nomina_it'],
	'version': '1.0',
	'description':"""Calculo de retenciones de 5ta categoria""",
	'auto_install': False,
	'demo': [],
	'data':	[
	'wizard/actualizar_proyecciones_view.xml',
	'hr_5percent.xml',
	'hr_uit_historical.xml',
	'hr_concepto_remunerativo.xml',
	'hr_five_category_view.xml',
	'hr_five_cat_prob_view.xml',
	'hr_five_cat_update_view.xml',
	],
	'installable': True
}
