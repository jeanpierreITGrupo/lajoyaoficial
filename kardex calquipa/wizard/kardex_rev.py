# -*- coding: utf-8 -*-
import openerp.addons.decimal_precision as dp
from openerp import models, fields
class kardex_resume(models.Model):
	_name = "kardex.resume"

	periodo = fields.Char(size=20,strign="Periodo")
	cta = fields.Char(size=200,strign="Cuenta")
	monto = fields.Float(digits=(20,2),string="Monto")
	contable=fields.Float(digits=(20,2),string="Contable")
	dif=fields.Float(digits=(20,2),string="Diferencia")

	_order = "periodo,cta"
kardex_resume()