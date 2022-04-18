# -*- encoding: utf-8 -*-
{
	'name': 'Gastos Vinculados IT',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE-BO',
	'depends': ['base_setup','stock','purchase'],
	'version': '1.0.0',
	'ITGRUPO_VERSION':4,
	'description': """
	- Gastos VInculados de Kardex
	- Sobreescribe el menu contabilidad -> purchase-> gastos vinculados
	- Se elige un proveedor y un proveedor de almacen para jalar las lineas y calcular prorateo
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/gastos_it_view.xml'],
	'installable': True
}
