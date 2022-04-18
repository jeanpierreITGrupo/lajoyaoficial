# -*- encoding: utf-8 -*-
{
	'name': 'Account Transfer IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account', 'res_users_it'],
	'version': '1.0',
	'description':"""
	Modulo de transferencias entre cajas(Diarios) con tipo de cambio personalizado
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_transfer_view.xml','security/it_grupo_security.xml',  'security/ir.model.access.csv'],
	'installable': True
}
