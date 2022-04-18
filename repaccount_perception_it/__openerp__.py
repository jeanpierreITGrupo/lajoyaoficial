# -*- encoding: utf-8 -*-
{
	'name': 'Repaccount Perception IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_contable_book_it','account_improve_sunat_it','account_parameter_it','account_move_sunat_it'],
	'version': '1.0',
	'description':"""
		Este modulo crea una vista para las percepciones y su expotacion en forma PI y P en csv
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_perception_wizard_view.xml','wizard/account_perception_view.xml'],
	'installable': True
}
