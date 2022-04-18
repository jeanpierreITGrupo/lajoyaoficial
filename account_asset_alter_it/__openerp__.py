# -*- encoding: utf-8 -*-
{
	'name': 'Account Asset Alter IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it','currency_sunat_change_it','partner_name_it','account_contable_book_it','repaccount_move_line_it'],
	'version': '1.0',
	'description':"""
	Personalizacion de Los Activos en COntabilidad:

	- Personalizacion de las vistas de acivos, categorias de activos y en las facturas de proveedores.
	- Cambios en su calculo de Depreciacion en los activos

	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_asset_alter_view.xml'],
	'installable': True
}
