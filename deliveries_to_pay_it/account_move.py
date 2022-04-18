# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class account_move(osv.osv):
	_name='account.move'
	_inherit='account.move'
	
	def _get_glosa(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		parameter_ids = self.pool.get('main.parameter').search(cr, uid, [])
		if len(parameter_ids) == 0:
			raise osv.except_osv('Alerta!', 'No existe el objeto Parametros en su configuracion contable. Contacte a su administrador')
		parametro = self.pool.get('main.parameter').browse(cr, uid, parameter_ids[0], context)
		
		for move in self.browse(cr, uid, ids, context=context):
			glosa = ''
			for line in move.line_id:
				if move.journal_id.currency:
					if line.account_id.id == parametro.deliver_account_me.id:
						glosa = line.name
				else:
					if line.account_id.id == parametro.deliver_account_mn.id:
						glosa = line.name
			
			result[move.id] = glosa
		return result

	def _get_divisa_deliver(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		parameter_ids = self.pool.get('main.parameter').search(cr, uid, [])
		if len(parameter_ids) == 0:
			raise osv.except_osv('Alerta!', 'No existe el objeto Parametros en su configuracion contable. Contacte a su administrador')
		
		parametro = self.pool.get('main.parameter').browse(cr, uid, parameter_ids[0], context)
		
		for move in self.browse(cr, uid, ids, context=context):
			glosa = None
			for line in move.line_id:
				if move.journal_id.currency:
					if line.account_id.id == parametro.deliver_account_me.id:
						glosa = line.currency_id.name
				else:
					if line.account_id.id == parametro.deliver_account_mn.id:
						glosa =  line.currency_id.name
			
			result[move.id] = glosa
		return result
		



	def _get_amount_currency_deliver(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		parameter_ids = self.pool.get('main.parameter').search(cr, uid, [])
		if len(parameter_ids) == 0:
			raise osv.except_osv('Alerta!', 'No existe el objeto Parametros en su configuracion contable. Contacte a su administrador')
		
		parametro = self.pool.get('main.parameter').browse(cr, uid, parameter_ids[0], context)
		
		for move in self.browse(cr, uid, ids, context=context):
			glosa = None
			for line in move.line_id:
				if move.journal_id.currency:
					if line.account_id.id == parametro.deliver_account_me.id:
						glosa = line.amount_currency
				else:
					if line.account_id.id == parametro.deliver_account_mn.id:
						glosa = line.amount_currency
			
			result[move.id] = glosa
		return result
		

	def _get_invoice(self, cr, uid, ids, field_name, arg, context=None):
		result = {}
		parameter_ids = self.pool.get('main.parameter').search(cr, uid, [])
		if len(parameter_ids) == 0:
			raise osv.except_osv('Alerta!', 'No existe el objeto Parametros en su configuracion contable. Contacte a su administrador')
		parametro = self.pool.get('main.parameter').browse(cr, uid, parameter_ids[0], context)
		
		for move in self.browse(cr, uid, ids, context=context):
			glosa = None
			for line in move.line_id:
				if move.journal_id.currency:
					if line.account_id.id != parametro.deliver_account_me.id:
						if glosa is None:
							glosa = line.nro_comprobante
						else:
							glosa = line.nro_comprobante
				else:
					if line.account_id.id != parametro.deliver_account_mn.id:
						if glosa is None:
							glosa = line.nro_comprobante
						else:
							glosa = line.nro_comprobante
			
			result[move.id] = glosa
		return result
		
	_columns = {
		'glosa_deliver' : fields.function(_get_glosa, type='char', string="Glosa"),
		'invoice_number' : fields.function(_get_invoice, type='char', string="Factura"),
		'amount_currency_deliver' : fields.function( _get_amount_currency_deliver, type='float', string='Importe Divisa' ),
		'divisa_deliver'  : fields.function( _get_divisa_deliver, type='char', string='Divisa' ),
	}
	
	"""
	def unlink(self,cr,uid,ids,context=None):
		for id in ids:
			cr.execute(""select balance_fixer_id from deliver_account_move_rel where account_move_id ='"" + str(id) + ""'"")
			vals = cr.dictfetchall()
			#raise osv.except_osv(_('Acción Inválida!'), vals)
			if len(vals) > 0:
				fixer = self.pool.get('deliveries.to.pay').browse(cr, uid, int(vals[0]['balance_fixer_id']), context)
				raise osv.except_osv('Acción Inválida!', 'No se puede eliminar un asiento contable que tenga relacionada la entrega a rendir Nro. ' + fixer.name )
		return super(account_move,self).unlink(cr,uid,ids,context)
	"""
account_move()

class account_move_line(osv.osv):
	_name='account.move.line'
	_inherit='account.move.line'
	
	def create(self, cr, uid, vals, context=None):
		if 'rendicion_id' in vals:
			print 'Inside'
			if vals['rendicion_id'] != False:
				cr.execute("""select name from deliveries_to_pay where id='""" + str(vals['rendicion_id']) + """'""")
				res = cr.dictfetchall()
				#raise osv.except_osv(_('Acción Inválida!'), res)
				
				vals.update({'rendicion_name': res[0]['name']})
		return super(account_move_line, self).create(cr, uid, vals, context)
	
	
	def write(self, cr, uid, ids, vals, context=None, check=False):
		if 'rendicion_id' in vals:
			print 'Inside'
			if vals['rendicion_id'] != False:
				cr.execute("""select name from deliveries_to_pay where id='""" + str(vals['rendicion_id']) + """'""")
				res = cr.dictfetchall()
				#raise osv.except_osv(_('Acción Inválida!'), res)
				
				vals.update({'rendicion_name': res[0]['name']})
		return super(account_move_line, self).write(cr, uid, ids, vals, context)
	
	_columns = {
		'rendicion_id': fields.many2one('deliveries.to.pay', string="Rendicion Id"),
		'rendicion_name': fields.char('Rendicion', size=64),
	}
	
account_move_line()