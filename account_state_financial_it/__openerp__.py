# -*- encoding: utf-8 -*-
{
	'name': 'Account State Financial IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_means_payment_it','account_sheet_work'],
	'version': '1.0',
	'description':"""
ESTADO DE SITUACION FINANCIERA : 	
	
1.-  CREAR UN MENU DENOMINADO CONFIGURACIÓN EE FF,  QUE ESTARÁ DENTRO DEL MENU CONTABILIDAD/CONFIGURACIÓN	
EN ESTE SUB MENU IRAN LOS SIGUIENTES SUBMENUS : 	
	
FORMATO BALANCE	
FORMATO RESULT. NATURALEZA	
FORMATO RESULT. POR FUNCIÓN 	
FORMATO CAMBIOS EN EL PATRIMONIO	
FORMATO FLUJOS DE EFECTIVO	
	
	
CADA UNO DE ESTOS SUBMENUS NOS PERMITIRAN INGRESAR A  UNA TABLA  EN LA QUE EL USUARIO IRA CREANDO LAS LÍNEAS QUE CONFORMAN EL ESTADO FINANCIERO	
Y EL RESPECTIVO CÓDIGO PARA QUE LUEGO SE ASOCIE ESE CÓDIGO A LA CUENTA CONTABLE Y SE TOTALICE PARA LA VISTA 	
	
A)  BALANCE GENERAL 	
	
	
ID	CONCEPTO 
1	EFECTIVO Y EQUIVALENTE DE DE EFECTIVO 
2	CUENTAS  POR COBRAR COMERCIALES 
3	EXISTENCIAS 
	
	
B) ESTADO DE RESULTADOS POR  NATURALEZA 	
	
ID	CONCEPTO 
1	VENTAS 
2	COSTO DE VENTAS 
3	COMPRAS 
	
C) ESTADO DE RESULTADOS POR  FUNCION 	
	
ID	CONCEPTO 
1	VENTAS 
2	COSTO DE VENTAS 
3	COMPRAS 
	
	
	
	
C) ESTADO DE FLUJOS DE EFECTIVO 	
	
ID	CONCEPTO
1	VENTA DE BIENES O SERVICIOS INGRESOS DE OPERACIONES
2	HONORARIOS Y COMISIONES 
3	INTERESES Y RENDIMIENTOS

	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_account_type_view.xml','wizard/account_state_financial_view.xml','wizard/account_state_efective_view.xml', 'wizard/account_patrimony_view.xml', 'wizard/account_state_nature_view.xml', 'wizard/account_state_function_view.xml', 'wizard/account_balance_general_view.xml','account_move_line_view.xml','account_voucher_view.xml','account_bank_statement_view.xml'],
	'installable': True
}
