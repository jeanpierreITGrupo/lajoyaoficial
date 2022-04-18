# -*- encoding: utf-8 -*-
{
	'name': 'Account Moorage Analytic IT',
	'category': 'Currency',
	'author': 'ITGrupo',
	'depends': ['account','base','analytic'],
	'version': '1.0',
	'description':"""
	CREAR ACA UN CAMPO DENOMINADO AMARRE AL DEBE 	
QUE ESTE DEBAJO DEL CAMPO CUANTA ANALITICA PADRE 	
Y QUE  PERMITA USAR LA CUENTA CONTABLE QUE CORRESPONDE A ESTA CUENTA	
ANALITICA .	
	
EL CAMPO DE AMARRE AL HABER SE COLOCARÁ EN LA PANTALLA DE CUENTAS CONTABLES 	

CREAR ACA UN CAMPO DE TIPO COMBO BOX 
DENOMINADO AMARRE AL HABER QUE SERVIRÁ PARA ELEGIR 
QUE CUENTA USARÁ DE MANERA PREDETERMINADA PARA SUS 
DESTINOS EN EL CREDIT 

	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_analytic_account_view.xml','account_account_view.xml'],
	'installable': True
}
