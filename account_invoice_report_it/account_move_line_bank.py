# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

def number_to_letter(number):
	UNIDADES = (
		'',
		'UN ',
		'DOS ',
		'TRES ',
		'CUATRO ',
		'CINCO ',
		'SEIS ',
		'SIETE ',
		'OCHO ',
		'NUEVE ',
		'DIEZ ',
		'ONCE ',
		'DOCE ',
		'TRECE ',
		'CATORCE ',
		'QUINCE ',
		'DIECISEIS ',
		'DIECISIETE ',
		'DIECIOCHO ',
		'DIECINUEVE ',
		'VEINTE '
	)

	DECENAS = (
		'VENTI',
		'TREINTA ',
		'CUARENTA ',
		'CINCUENTA ',
		'SESENTA ',
		'SETENTA ',
		'OCHENTA ',
		'NOVENTA ',
		'CIEN '
	)

	CENTENAS = (
		'CIENTO ',
		'DOSCIENTOS ',
		'TRESCIENTOS ',
		'CUATROCIENTOS ',
		'QUINIENTOS ',
		'SEISCIENTOS ',
		'SETECIENTOS ',
		'OCHOCIENTOS ',
		'NOVECIENTOS '
	)

	MONEDAS = (
		{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
		{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
		{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
		{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
		{'country': u'Perú', 'currency': 'PEN', 'singular': u'SOL', 'plural': u'SOLES', 'symbol': u'S/.'},
		{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
	)
	# Para definir la moneda me estoy basando en los código que establece el ISO 4217
	# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
	# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

	def __convert_group(n):
		"""Turn each group of numbers into letters"""
		output = ''

		if(n == '100'):
			output = "CIEN"
		elif(n[0] != '0'):
			output = CENTENAS[int(n[0]) - 1]

		k = int(n[1:])
		if(k <= 20):
			output += UNIDADES[k]
		else:
			if((k > 30) & (n[2] != '0')):
				output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			else:
				output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
		return output
	#raise osv.except_osv('Alerta', number)
	number=str(round(float(number),2))
	separate = number.split(".")
	number = int(separate[0])

	if int(separate[1]) >= 0:
		moneda = "con " + str(separate[1]).ljust(2,'0') + "/" + "100 " 

	"""Converts a number into string representation"""
	converted = ''
	
	if not (0 <= number < 999999999):
		raise osv.except_osv('Alerta', number)
		#return 'No es posible convertir el numero a letras'

	
	
	number_str = str(number).zfill(9)
	millones = number_str[:3]
	miles = number_str[3:6]
	cientos = number_str[6:]
	

	if(millones):
		if(millones == '001'):
			converted += 'UN MILLON '
		elif(int(millones) > 0):
			converted += '%sMILLONES ' % __convert_group(millones)

	if(miles):
		if(miles == '001'):
			converted += 'MIL '
		elif(int(miles) > 0):
			converted += '%sMIL ' % __convert_group(miles)

	if(cientos):
		if(cientos == '001'):
			converted += 'UN '
		elif(int(cientos) > 0):
			converted += '%s ' % __convert_group(cientos)
	if float(number_str)==0:
		converted += 'CERO '
	converted += moneda

	return converted.upper()




class account_invoice(models.Model):
	_inherit ='account.invoice'


	@api.multi
	def do_imprimir_factura(self):

		config_print = self.env['config.print.factura'].search([])

		txt = chr(27)+chr(15)+chr(27)+chr(48)
		if config_print and len(config_print)>0 and config_print[0]:
			exec(config_print[0].texto_cabezera)
			exec(config_print[0].texto_cuerpo)
			exec(config_print[0].texto_pie)

		txt +=chr(12)+chr(27)
		self.env['make.txt'].makefile(txt,'prtfactura')



class config_print_factura(models.Model):
	_name = 'config.print.factura'

	texto_cabezera = fields.Text('Formato de Impresión Cabecera')
	texto_cuerpo = fields.Text('Formato de Impresión Cuerpo')
	texto_pie = fields.Text('Formato de Impresión Pie')

	_defaults={
		'texto_cabezera': """import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
txt += '\\n'*22
txt += ' '*85 + str(self.date_invoice).split('-')[2] + '                  '+ str(self.date_invoice).split('-')[1] +'             '    + str(self.date_invoice).split('-')[0]+ '\\n\\n\\n'
txt += ' '*20 + str(self.partner_id.name) + '\\n\\n\\n'
txt += ' '*20 + str(self.partner_id.type_number if self.partner_id.type_number else '').ljust(85) + str(self.origin if self.origin else '') +'\\n\\n'
txt += ' '*20 + str(self.partner_id.street if self.partner_id.street else '') + '\\n\\n\\n\\n\\n\\n\\n'""",


		'texto_cuerpo': """lineas = 39
contador = 0
for i in self.invoice_line:
	if contador <lineas:
		if i.product_id.id:
			txt += ' '*9 +str(i.product_id.default_code if i.product_id.default_code else '')[:11].ljust(11)
		else:
			txt +=' '*20
		txt += str(i.quantity)[:10].rjust(10)
		if i.uos_id.id:
			txt += ' '*2 +str(i.uos_id.name)[:10].ljust(10)
		else:
			txt += ' '*12
		txt += '  '+ str(i.name)[:50].ljust(50)
		txt += ("%0.2f"% i.price_unit).rjust(15)
		txt += ("%0.2f"% i.price_subtotal).rjust(16) + "\\n"
		contador += 1
		sobra = str(i.name)[50:]
		while sobra != '':
			txt += ' '*44 + sobra[:50] + "\\n"
			sobra = sobra[50:]
			contador += 1
for j in range(0, lineas-contador):
	txt += '\\n'""",


		'texto_pie': """txt += chr(27)+chr(71)+ ' '*109 + ("%0.2f"% self.amount_untaxed).rjust(16)+ "\\n\\n" + chr(27)+chr(72)
txt += chr(27)+chr(71)+ ' '*109 + ("%0.2f"% self.amount_tax).rjust(16)+ "\\n" + chr(27)+chr(72)
txt += ' '*9 +number_to_letter(self.amount_total).ljust(90)   +  ' '*10 +chr(27)+chr(71)+  ("%0.2f"% self.amount_total).rjust(16)+ "\\n" + chr(27)+chr(72)
""",
	}