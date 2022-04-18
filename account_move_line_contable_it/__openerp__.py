# -*- encoding: utf-8 -*-
{
	'name': 'Account Move Line Contable IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it','currency_sunat_change_it','partner_name_it'],
	'version': '1.0',
	'description':"""
	Agregar 2 campos a la vista tree de apuntes contables,
	y como filtro tambien 
	tipo de documento 
	y comprobante

	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_line_contable_view.xml'],
	'installable': True
}
