# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class make_exchange_diff(osv.osv_memory):
	_name = "make.exchange.diff"
	_columns = {
		'journal_id': fields.many2one('account.journal', 'Diario'),
		'has_extorno': fields.boolean('Tiene Extorno'),
	}
	
	_defaults = {
		'has_extorno': True,
	}
	
	def view_init(self, cr, uid, fields_list, context=None):
		if context is None:
			context = {}
		record_id = context and context.get('active_id', False)
		return False

	def make_calculate_differences(self, cr, uid, ids, context=None):
		line_obj = self.pool.get('exchange.diff.line')
		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		if context is None:
			context = {}
		# for install_act in picking_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
			# if install_act.state == 'draft':
			# 	raise osv.except_osv('Alerta', 'No es posible procesar notas en borrador')
		data = self.read(cr, uid, ids, [], context=context)[0]
		#print 'Fecha Fin', data['date_end']
		context.update({'journal_id': data['journal_id'][0], 'has_extorno': data['has_extorno']})
						
		ids2=line_obj.make_calculate_differences(cr, uid, context.get(('active_ids'), []), context)
		if ids2==[]:
			raise osv.except_osv('Alerta','No se calculo la diferencias, verifique que los elementos seleccionados')
		result={}
		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'exchange_diff_it','view_exchange_diff_line_action')
		# raise osv.except_osv('Alerta', view_ref[1])		
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read(cr, uid, [view_id], context=context)[0]
		return result
		
make_exchange_diff()