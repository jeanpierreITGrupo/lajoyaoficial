# -*- encoding: utf-8 -*-
{
	'name': 'Analytic Accoun in Product IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account_analytic_default', 'product', 'purchase'],
	'version': '1.0',
	'description':"""
	AGREGAR EN LA PESTAÑA CONTABILIDAD DE LOS PRODUCTOS UN CAMPO PARA QUE EL USUARIO ASIGNE LA CUENTA ANALITICA POR DEFECTO QUE VA A TENER ESE PRODUCTO 
DICHO CAMPO SOLO ESTARÁ ACTIVO SI EL PRODUCTO ES DISTINTO A ALMACENABLE,  Y SE COPIARA A LA FACTURA GENERADA O PEDIDO DE COMPRA CUANDO SE SELECCIONE UN PRODUCTO
	""",
	'auto_install': False,
	'demo': [],
	'data':	['product_product_view.xml'],
	'installable': True
}
