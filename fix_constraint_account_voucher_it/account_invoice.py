# -*- coding: utf-8 -*-

from openerp import models, fields, api ,  _
from openerp.osv import osv

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	def unlink(self,cr,uid,ids,context=None):
		#raise osv.except_osv( 'Alerta!', "No se puede eliminar una factura que ya ha sido validada!")
		data = self.read(cr, uid, ids, context=context)
		for i in data:
			if 'internal_number' in i:
				if i['internal_number']:
					print "existes"
					print i['internal_number']
					raise osv.except_osv( 'Alerta!', "No se puede eliminar una factura que ya ha sido validada!")

		return super(account_invoice,self).unlink(cr,uid,ids,context=context)