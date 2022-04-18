# -*- encoding: utf-8 -*-
{
	'name': 'Saldos_de_apertura',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_contable_book_it'],
	'version': '1.0',
	'description':"""
	Módulo 	que traslada los saldos de las cuentas por cobrar y por pagar al siguiente ejercicio,  añade tambien la opcion de desconciliar en el botón mas de asientos contables.	
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_contable_fch_wizard_view.xml'],
	'installable': True
}
