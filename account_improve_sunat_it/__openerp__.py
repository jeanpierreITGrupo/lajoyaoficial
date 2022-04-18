# -*- encoding: utf-8 -*-
{
	'name': 'Account Improve Sunat IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it'],
	'version': '1.0',
	'description':"""
		AGREGAR A FACTURAS DE PROVEEDOR,  FACTURAS DE  CLIENTES Y FACTURAS RECTIVICATIVAS ( CLIENTE Y PROVEEDOR )   EN UNA PESTAÑA DENOMINADA SUNAT LOS SIGUIENTES CAMPOS :  									
									
COMPROBANTE DETRACCION									
Fecha Comprobante : 									
Numero Comprobante: 									
Monto: 									
									
FECHA :	ES CAMPO DE TIPO DATE 								
NÚMERO DE COMPROBANTE :			CAMPO DE TIPO TEXTO DE 30 DE ANCHO 						
MONTO : 	CAMPO DE TIPO NÚMERICO CON DOS DECIMALES								
									
ESTOS TRES CAMPOS SE AÑADEN A LA TABLA, ACCOUNT_INVOICE									
									
									
AGREGAR EN FACTURAS DE CLIENTES, FACTURAS DE PROVEEDOR Y FACTURAS RECTIFICATIVAS ( CLIENTE O  PROVEEDOR)   EN LA PESTAÑA SUNAT UNA  GRILLA  									
PARA PODER AÑADIR LOS DOCUMENTOS QUE ESTAN SIENDO MODIFICADOS 									
									
									al hacer click en el botíon agregar llamará a la lista de  facturas de proveedor 
									si se esta en factura rectivicativa de proveedor o facturas de proveedor 
									y a la de facturas de clientes si se esta en una factura rectificativa de clientes 
									o factura rectificativa de clientes
									solo añade la información de esas fcaturas no hace ningún otro proceso 
									
									LA GRILLA VA EN LA PARTE INFERIOR DEBAJO DE LOS DATOS DE COMPROBANTE DE 
									DETRACCIÓN,  POSTERIORMENTE VAMOS A AÑADIR OTROS CAMPOS EN ESTA PESTAÑA 

	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_invoice_view.xml'],
	'installable': True
}
