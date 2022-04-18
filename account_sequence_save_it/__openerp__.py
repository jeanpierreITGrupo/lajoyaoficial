# -*- encoding: utf-8 -*-
{
	'name': 'Account Sequence Save IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher'],
	'version': '1.0',
	'description':"""
       Los objetos que deben mantener las secuencias son los siguientes :  account voucher (pagos a proveedores y pagos de clientes).   Entregas a rendir ( asiento de entrega),  transferencias.
       siempre el asiento que creen deberá mantenerse y una vez validados esos objetos ya no podrán eliminarse
	""",
	'auto_install': False,
	'demo': [],
	'data':	[],
	'installable': True
}
