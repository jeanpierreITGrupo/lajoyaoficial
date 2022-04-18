# -*- encoding: utf-8 -*-
{
	'name': 'Account Means Payment IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it','currency_sunat_change_it'],
	'version': '1.0',
	'description':"""
		Modulo:
		EN PAGOS  DE CLIENTES,  PAGOS A PROVEEDORES,   ESCRIBIR CHEQUES Y EXTRACTOS BANCARIOS ,  pagos desde factura										
	CONFIGURACION/TABLAS SUNAT									
1.-	Agregar  un campo denominado  medio de pago  de tipo combobox para elegir el medio de pago usado ,  se scará la información de una tabla 									
	denominada  medio_pago   que tendrá  los siguientes campos ( id,  codigo char(3), descripción char(3))									
										
2.-	Para elegir se mostrará  un combobox en los asistentes ( pagos de clientes, pagos de proveedores, escribir cheques, y extractos bancarios) donde se elegirá el medio de pago 									
	muestra la descripción pero lo que graba es el código en la base en un campo que se llamará MPAGO y que estará  en la tabla account_move_line									
										
3.- 	Este campo  sera mostrado también en cada una de las líneas de asiento contable, ira  luego del campo tipo de documento , y se podra seleccionar de un combobox 									
	aquí al elegir uno de la lista solo se mostrará su código, nunca la descripción									
										
4.- tomar en cuenta que los extractos bancarios generan varios objetos  de tipo account_voucher cada uno de ellos herreda el medio de pago que se selecciono en el extracto bancario 										
										
5.- 	tomar en cuenta también que el medio de pago seleccionado solo se pegará en la línea que ocntenga la cuenta de caja configurada es decir la cuenta de tipo efectivo que corresponde al metodo de pago 									
	o diario seleccionado.									
										
	EJEMPLO :   PARA PAGAR UNA CUENTA DE CAJA SE ELIGE COMO METODO DE PAGO CAJA MONEDA NACIONAL ( CUYA CUENTA PREDETERMINADA ES 10111)  Y EL  MEDIO DE PAGO QUE 									
	SE SELECCIONO ES  CHEQUES NO NEGOCIABLES QUE TIENE COMO CÓDIGO 007)   EL PAGO ES DE UNA FACTURA  POR 4000.00 SOLES 									
										
	EL ASIENTO SERA DE MOSTRADPO DE ESTA FORMA : 									
										
	NOMBRE	EMPRESA	REFERENCIA	CUENTA	DEBE	HABER	DIVISA	IMPORTE DIVISA	TIPO DOCUM	MPAGO
	PAGO FACTURA	LAYCONSA SAC	0001-789	4212	4000				01	
	PAGO FACTURA	LAYCONSA SAC	0001-789	10111		4000				007
										
6.-	EL USUARIO NO ESTARÁ OBLIGADO A INGRESAR INFORMACIÓN PARA ESTE CAMPO EN NINGUNO DE LOS  FORMULARIOS EN LOS QUE ESTE INCLUIDO									

	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_voucher_view.xml','account_bank_statement_view.xml','account_move_line_view.xml'],
	'installable': True
}
