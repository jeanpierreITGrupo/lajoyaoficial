# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class account_move(models.Model):
	_inherit='account.move'
	check_daot = fields.Boolean('Es operación externa')


class account_invoice(models.Model):
	_inherit='account.invoice'
	check_daot = fields.Boolean('Es operación externa')
	
	@api.one
	def action_number(self):
		t = super(account_invoice,self).action_number()
		for inv in self:
			if inv.check_daot:
				self._cr.execute(""" UPDATE account_move SET check_daot=true WHERE id=""" + str(inv.move_id.id))
		return t


class daot_register(models.Model):
	_name='daot.register'
	
	type_operation =  fields.Selection([('costo','Costo'),('ingreso','Ingreso')], 'Tipo Operación')
	tipo_doc = fields.Many2one('it.type.document','Tipo Doc.')
	divisa = fields.Many2one('res.currency','Moneda')
	partner_id = fields.Many2one('res.partner','Partner')
	ruc = fields.Char('RUC',size=50)
	razonsocial = fields.Char('Razon Social',size=200)
	date_ini = fields.Date('Fecha Adq.')
	date_fin = fields.Date('Fecha Ven.')
	serie = fields.Char('Serie',size=200)
	numero = fields.Char('Número',size=200)
	base = fields.Float('Base',digits=(12,3))
	igv = fields.Float('IGV.',digits=(12,3))
	total = fields.Float('Total',digits=(12,3))


class daot_register_wizard(osv.TransientModel):
	_name='daot.register.wizard'
	
	check = fields.Boolean("check")
	mensaje = fields.Char("mensaje", size=200)
	type_operation =  fields.Selection([('costo','Costo'),('ingreso','Ingreso')], 'Tipo Operación')
	tipo_doc = fields.Many2one('it.type.document','Tipo Doc.')
	divisa = fields.Many2one('res.currency','Moneda')
	partner_id = fields.Many2one('res.partner','Partner')
	ruc = fields.Char('RUC',size=50)
	razonsocial = fields.Char('Razon Social',size=200)
	date_ini = fields.Date('Fecha Adq.')
	date_fin = fields.Date('Fecha Ven.')
	serie = fields.Char('Serie',size=200)
	numero = fields.Char('Número',size=200)
	base = fields.Float('Base',digits=(12,3))
	igv = fields.Float('IGV.',digits=(12,3))
	total = fields.Float('Total',digits=(12,3))
	
	@api.onchange("partner_id")
	def onchange_partner_id(self):
		if self.partner_id:
			self.razonsocial = self.partner_id.name
			self.ruc = self.partner_id.type_number

	@api.onchange("date_ini")
	def onchange_date_ini(self):
		if self.date_ini:
			self.date_fin = self.date_ini

	@api.onchange("base","igv")
	def onchange_base_igv(self):
		self.total = self.base + self.igv

	@api.multi
	def do_rebuild(self):
		data = {
		'type_operation' : self.type_operation ,
		'tipo_doc' :self.tipo_doc.id ,
		'divisa' :self.divisa.id ,
		'partner_id' :self.partner_id.id ,
		'ruc' :self.partner_id.type_number ,
		'razonsocial' :self.partner_id.name ,
		'date_ini' :self.date_ini ,
		'date_fin' :self.date_fin ,
		'serie' :self.serie ,
		'numero' :self.numero ,
		'base' :self.base ,
		'igv' :self.igv ,
		'total' :self.base + self.igv ,
		}
		print data
		self.env['daot.register'].create(data)
		return {
			'context': {'default_check':True,'default_mensaje': 'Registrado exitosamente el "'+data['type_operation'] + '" con Monto Total: ' + str(data['total']) },
			'type': 'ir.actions.act_window',
			'res_model': 'daot.register.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target': 'new',
		}
