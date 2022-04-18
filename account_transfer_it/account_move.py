# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
from openerp import models

class account_move(osv.osv):
	_name='account.move'
	_inherit='account.move'
	
	"""
	def unlink(self,cr,uid,ids,context=None):
		for id in ids:
			cr.execute(""select transfer_id from transfer_account_move_rel where account_move_id ='"" + str(id) + ""'"")
			vals = cr.dictfetchall()
			#raise osv.except_osv(_('Acción Inválida!'), vals)
			if len(vals) > 0:
				transfer = self.pool.get('account.transfer').browse(cr, uid, int(vals[0]['transfer_id']), context)
				raise osv.except_osv('Acción Inválida!', 'No se puede eliminar un asiento contable que tenga relacionada la transferencia Nro. ' + transfer.name )
		return super(account_move,self).unlink(cr,uid,ids,context)
	"""
account_move()
