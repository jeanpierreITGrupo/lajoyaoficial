# -*- encoding: utf-8 -*-
{
	'name': 'Account Invoice Series',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account_tables_it', 'account_type_doc_it'],
	'version': '1.0',
	'description':"""
	V1.0
		Agrega las secuencias de acuerdo al tipo de documentos en las Facturas de cliente y Rectificativas
	""",
	'auto_install': False,
	'demo': [],
	'data':['it_invoice_serie_view.xml', 'account_invoice_view.xml'],
	'installable': True
}