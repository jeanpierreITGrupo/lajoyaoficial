# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
import logging
from openerp.osv import orm
from openerp.tools.translate import _
import datetime
import base64
_logger = logging.getLogger(__name__)

class selection_wizard(osv.osv_memory):
	_name='selection.wizard'
	
	TYPE_SELECTION = [
		('payable', 'A Pagar'),
		('receivable', 'A Cobrar'),
		('asset', 'Activos'),
		('liability', 'Pasivos'),
	]
	
	_columns={
		'fiscalyear_id': fields.many2one('account.fiscalyear', 'Anio Fiscal'),
		'period_id': fields.many2one('account.period', 'Periodo'),
		'type': fields.selection(TYPE_SELECTION, 'Tipo'),
	}
	
	def print_report(self, cr, uid, ids, context=None):
		line_obj = self.pool.get('exchange.diff.line')
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		
		if context == None:
			context = {}
		data = self.read(cr, uid, ids, [], context=context)[0]
		#print 'Fecha Fin', data['date_end']
		context.update({'fiscalyear_id': data['fiscalyear_id'][0], 'period_id': data['period_id'][0], 'type': data['type']})
		
		cr.execute('TRUNCATE exchange_diff_line;')
		
		ids2=line_obj.make_process_records(cr, uid, context)
		if ids2==[]:
			raise osv.except_osv('Alerta','No encontraron registros')
		result={}
		#raise osv.except_osv('Alerta',data)
		view_ref = False
		if data['type'] in ['payable', 'receivable']:
			print 'IN 1'
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'exchange_diff_it', 'view_exchange_diff_line_action')
			view_id = view_ref and view_ref[1] or False
			print 'view_id', view_id
			result = act_obj.read(cr, uid, [view_id], context=context)
			print 'result', result
			return result[0]
		else:
			print 'IN 2'
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'exchange_diff_it', 'view_exchange_diff_line_active_action')
			view_id = view_ref and view_ref[1] or False
			print 'view_id', view_id
			result = act_obj.read(cr, uid, [view_id], context=context)
			print 'result', result
			return result[0]
			
		# raise osv.except_osv('Alerta', view_ref[1])	
	
selection_wizard()