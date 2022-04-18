# -*- coding: utf-8 -*-
import pprint
import itertools
import openerp.addons.decimal_precision as dp

from lxml import etree

from openerp.osv import osv
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare

class account_invoice(models.Model):
	_inherit = "account.invoice"
	
	is_fixer = fields.Boolean('No mueve cantidades')
	
	@api.one
	def action_number(self):
		t = super(account_invoice,self).action_number()
		self.write({})
		for inv in self:
			if inv.is_fixer:
				self._cr.execute( 'UPDATE account_move_line SET quantity = 0 WHERE move_id=' + str(inv.move_id.id))
		for inv in self:
			if inv.is_fixer:
				for i in inv.invoice_line:
					self._cr.execute( 'UPDATE account_invoice_line SET quantity = 0 WHERE id=' + str(i.id))
		return t
	
	
	@api.model
	def line_get_convert(self, line, part, date):
		import pprint
		pprint.pprint(line)
		t = super(account_invoice,self).line_get_convert(line,part,date)
		if 'invl_id' in line:
			t['location_id'] = self.env['account.invoice.line'].search([('id','=',line['invl_id'])])[0].location_id.id
		return t

class account_invoice_line(models.Model):

	_inherit = "account.invoice.line"	
	location_id = fields.Many2one('stock.location', 'Ubicacion')
	

