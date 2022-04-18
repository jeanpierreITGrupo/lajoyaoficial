# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_purchase_register_nodeducible(models.Model):
	_name = 'account.purchase.register.nodeducible'
	_auto = False

	periodo= fields.Char('Periodo', size=50)
	libro= fields.Char('Libro', size=50)
	voucher= fields.Char('Voucher', size=50)
	fecha = fields.Date('Fecha')

	type_number = fields.Char('RUC/DNI.', size=50)
	tdp = fields.Char('T.D.P.', size=50)
	empresa = fields.Char('Razon Social', size=50)
	tc = fields.Char('T.C')
	nro_comprobante = fields.Char('Nro. Comprobante', size=50)
	
	
	base1 = fields.Float('BIOGE', digits=(12,2))
	base2 = fields.Float('BIOGENG', digits=(12,2))
	base3 = fields.Float('BIONG', digits=(12,2))
	cng = fields.Float('CNG', digits=(12,2))
	isc = fields.Float('ISC', digits=(12,2))
	igv1 = fields.Float('IGVA', digits=(12,2))
	igv2 = fields.Float('IGVB', digits=(12,2))
	igv3 = fields.Float('IGVC', digits=(12,2))
	otros  = fields.Float('Otros', digits=(12,2))
	total  = fields.Float('Total', digits=(12,2))
	motivo_rep = fields.Char('motivo_rep', size=50)
	beneficiario = fields.Char('Beneficiario')
	