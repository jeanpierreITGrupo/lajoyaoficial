# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
import logging
from openerp.osv import orm
from openerp.tools.translate import _
import datetime
import base64
_logger = logging.getLogger(__name__)

class finantial_convertion_wizard(osv.osv_memory):
	_name='finantial.conversion.wizard'
	
	_columns={
		'period_id': fields.many2one('account.period', 'Periodo'),
	}
	
	def print_report(self, cr, uid, ids, context=None):
		line_obj = self.pool.get('account.move.line')
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		
		if context == None:
			context = {}
		data = self.read(cr, uid, ids, [], context=context)[0]
		#print 'Fecha Fin', data['date_end']
		context.update({'period_id': data['period_id'][0]})
		
		ids2=line_obj.update_me_fields(cr, uid, context)
		if ids2==[]:
			raise osv.except_osv('Alerta','No encontraron registros')
		result={}
		#raise osv.except_osv('Alerta',data)

		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'action_move_journal_line')
		view_id = view_ref and view_ref[1] or False
		print 'view_id', view_id
		result = act_obj.read(cr, uid, [view_id], context=context)
		print 'result', result
		return result[0]
		# raise osv.except_osv('Alerta', view_ref[1])		
		
	
finantial_convertion_wizard()