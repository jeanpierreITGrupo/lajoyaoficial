# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	period_perception_id = fields.Many2one('account.period','Periodo Uso Percepcion')

	@api.one
	def write(self,vals):
		if self.type == 'in_invoice' or self.type == 'in_refund':
			if self.period_perception_id.id:
				pass
			else:
				if self.period_id.id:
					vals['period_perception_id'] = self.period_id.id
		t = super(account_invoice,self).write(vals)

		if self.type == 'in_invoice' or self.type == 'in_refund':
			for inv in self:
				if inv.move_id.id:
					if inv.period_perception_id.id:
						self._cr.execute(""" UPDATE account_move SET period_perception_id='%s' WHERE id=%s """%(inv.period_perception_id.id, inv.move_id.id))
					else:
						self._cr.execute(""" UPDATE account_move SET period_perception_id=Null WHERE id=%s """%(inv.move_id.id))
		return t


	@api.one
	def action_number(self):
		t = super(account_invoice,self).action_number()
		
		if self.type == 'in_invoice' or self.type == 'in_refund':
			
			if self.period_perception_id.id:
				pass
			else:
				if self.period_id.id:
					self.period_perception_id = self.period_id.id
			self.write({'period_perception_id': self.period_id.id})
			for inv in self:
				if inv.move_id.id:
					if inv.period_perception_id.id:
						self._cr.execute(""" UPDATE account_move SET period_perception_id='%s' WHERE id=%s """%(inv.period_perception_id.id, inv.move_id.id))
					else:
						self._cr.execute(""" UPDATE account_move SET period_perception_id=Null WHERE id=%s """%(inv.move_id.id))
		return t


class account_move(models.Model):
	_inherit = 'account.move'

	period_perception_id = fields.Many2one('account.period','Periodo Uso Percepcion')
