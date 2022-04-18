# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _

class account_move(models.Model):
	_inherit='account.move'

	@api.model
	def create(self,vals):		
		t = super(account_move,self).create(vals)
		if t.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		return t 


	@api.one
	def copy(self,default=None):
		if self.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		return super(account_move,self).copy(default) 


	@api.one
	def write(self, vals):
		m = super(account_move,self).write(vals)
		self.refresh()
		if self.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		
		return m

	@api.one
	def button_cancel(self):
		if self.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		return super(account_move,self).button_cancel()



	@api.one
	def unlink(self):
		if self.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.)")
		return super(account_move,self).unlink()



class account_move_line(models.Model):
	_inherit='account.move.line'

	@api.model
	def create(self,vals):		

		t = super(account_move_line,self).create(vals)
		if t.move_id.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		return t 


	@api.one
	def copy(self,default=None):
		if self.move_id.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		return super(account_move_line,self).copy(default) 


	@api.one
	def write(self,vals,check=True, update_check=True):
		if 'reconcile_id' in vals or 'reconcile_partial_id' in vals and len(vals.keys()) == 1:
			return super(account_move_line,self).write(vals,check=check,update_check=update_check)
		
		m = super(account_move_line,self).write(vals,check=check,update_check=update_check)
		self.refresh()
		if self.move_id.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		
		return m

	@api.one
	def unlink(self):
		if self.move_id.period_id.state == 'done':
			raise osv.except_osv('Alerta!', u"El periodo seleccionado se encuentra cerrado.")
		return super(account_move_line,self).unlink()
