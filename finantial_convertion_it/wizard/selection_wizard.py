# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class selection_wizard(osv.TransientModel):
	_name='selection.wizard'
	
	TYPE_SELECTION = [
		('payable', 'A Pagar'),
		('receivable', 'A Cobrar'),
		('asset', 'Activos'),
		('liability', 'Pasivos'),
	]
	
	period_id = fields.Many2one('account.period','Periodo')
	type_show =  fields.Selection(TYPE_SELECTION, 'Tipo')
	
	@api.multi
	def print_report(self):
		line_obj = self.env['exchange.diff.line']
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		
		period_id = self.period_id
		tipo = self.type_show
		
		self.env.cr.execute('TRUNCATE exchange_diff_line;')
		
		ids2=line_obj.make_process_records(period_id.id, tipo)
		if ids2==[]:
			raise osv.except_osv('Alerta','No encontraron registros')
		result={}
		#raise osv.except_osv('Alerta',data)
		view_ref = False
		if self.type_show in ['payable', 'receivable']:
			print 'IN 1'
			view_ref = self.pool.get('ir.model.data').get_object_reference(self.env.cr, self.env.uid, 'exchange_diff_it', 'view_exchange_diff_line_action')
			view_id = view_ref and view_ref[1] or False
			print 'view_id', view_id
			result = act_obj.read(self.env.cr, self.env.uid, [view_id], context=self.env.context)
			print 'result', result
			return result[0]
		else:
			print 'IN 2'
			view_ref = self.pool.get('ir.model.data').get_object_reference(self.env.cr, self.env.uid, 'exchange_diff_it', 'view_exchange_diff_line_active_action')
			view_id = view_ref and view_ref[1] or False
			print 'view_id', view_id
			result = act_obj.read(self.env.cr, self.env.uid, [view_id], context=self.env.context)
			print 'result', result
			return result[0]
			
		# raise osv.except_osv('Alerta', view_ref[1])	
	