# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class make_exchange_diff(models.Model):
	_name = "make.exchange.diff"

	journal_id = fields.Many2one('account.journal', 'Diario')
	'''
	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		record_id = context and context.get('active_id', False)
		return False
	'''
	@api.multi
	def make_calculate_differences(self):
		line_obj = self.env['exchange.diff.line']
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		
		journal_id = self.journal_id
		
		ids2 = line_obj.make_calculate_differences(journal_id.id)
		if ids2==[]:
			raise osv.except_osv('Alerta','No se calculo la diferencias, verifique que los elementos seleccionados')
		result={}
		view_ref = self.pool.get('ir.model.data').get_object_reference(self.env.cr, self.env.uid, 'exchange_diff','view_exchange_diff_line_action')
		# raise osv.except_osv('Alerta', view_ref[1])		
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read(self.env.cr, self.env.uid, [view_id], self.env.context)[0]
		return result
