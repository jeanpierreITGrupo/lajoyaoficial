# -*- encoding: utf-8 -*-
{
	'name': 'modbase IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['web'],
	'version': '1.0',
	'description':"""
	Nuevo Modulo Base que impide la modificacion de las estrucuras Many2one en todas las tablas a excepcion de:
	account_move en las facturas
	""",
	'auto_install': False,
	'demo': [],
	'js':['static/src/js/mywidget.js'], 
	'data':	['security/purchase_national_security.xml','modbase_it_view.xml'],
	'installable': True
}
