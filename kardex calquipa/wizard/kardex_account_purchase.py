# -*- coding: utf-8 -*-
import openerp.addons.decimal_precision as dp
from openerp import models, fields
class kardex_account_purchase(models.Model):
	_name = "kardex.account.purchase"

	periodo = fields.Char(size=20,string="Periodo")
	fecha = fields.Date(string="Fecha")
	libro = fields.Char(size=50,string="Libro")
	voucher = fields.Char(size=20,string="Voucher")
	td = fields.Char(size=2,string="TD")
	serie = fields.Char(size=4,string="Serie")
	numero  = fields.Char(size=20,string=u"Número")
	proveedor = fields.Char(size=200,string="Proveedor")
	producto = fields.Char(size=200,string="Producto")
	base = fields.Float(digits=(20,2),string="Base")
	valor_factura = fields.Float(digits=(20,2),string="Valor Factura")
	diferencia = fields.Float(digits=(20,2),string="Diferencia")

	_order = "periodo,proveedor,fecha,libro,voucher"


kardex_account_purchase()