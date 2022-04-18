# -*- encoding: utf-8 -*-
import base64
import codecs
import pprint

from openerp.osv import osv
from openerp import models, fields, api
from datetime import datetime, date, time, timedelta

class fees_report(osv.TransientModel):
	_name = "fees.report"

	@api.multi
	def get_fees(self):
		import sys
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		
		filtro = [('id', 'in', self.env.context.get(('active_ids'), []))]
		#raise osv.except_osv('Alerta',filtro)
		inside = []

		recibos = self.env['account.forth.category'].search(filtro)
		
		parser = {
			'02' : 'R',
			'07' : 'N',
			'D' : 'D',
			'00' : 'O',
		}
		
		ctxt=""
		periodo = None
		n=0
		separator = '|'
		in_ids = []
		for recibo in recibos:
			if periodo != recibo.periodo and periodo is not None:
				raise osv.except_osv('Alerta','Hay periodos distintos en la consulta')
			periodo = recibo.periodo
			has_ret = '1' if recibo.retencion != 0 else '0'
			com_type = parser[recibo.tipodocumento]
			n = n+1

			ctxt += recibo.tipodoc + separator
			ctxt += recibo.numdoc + separator
			ctxt += com_type + separator
			ctxt += recibo.serie + separator
			ctxt += recibo.numero + separator
			ctxt += str(recibo.monto) + separator
			ctxt += datetime.strptime(recibo.fechaemision, '%Y-%m-%d').strftime('%d/%m/%Y') + separator
			ctxt += datetime.strptime(recibo.fechapago, '%Y-%m-%d').strftime('%d/%m/%Y') + separator
			ctxt += has_ret + separator
			ctxt += separator
			ctxt += separator
			ctxt=ctxt+"""\r\n"""

		code = '0601'
		periodo = periodo.split('/')
		name = periodo[1]+periodo[0]
		user = self.env['res.users'].browse(self.env.uid)
		print 'name', name
		print 'user', user
		if user.company_id.id == False:
			raise osv.except_osv('Alerta','El usuario actual no tiene una compañia asignada. Contacte a su administrador.')
		if user.company_id.partner_id.id == False:
			raise osv.except_osv('Alerta','La compañia del usuario no tiene una empresa asignada. Contacte a su administrador.')
		if user.company_id.partner_id.type_number == False:
			raise osv.except_osv('Alerta','La compañia del usuario no tiene un numero de documento. Contacte a su administrador.')
			
		ruc = user.company_id.partner_id.type_number
		
		print 'ruc', ruc
		file_name = code + name + ruc + '.4ta'
		
		vals = {
			'output_name': file_name,
			'output_file': base64.encodestring(ctxt),		
		}
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}
	
	'''
	def make_process_records(self, cr, uid, ids, context=None):
		#ruc = '20154875658'
		parser = {
			'02' : 'R',
			'07' : 'N',
			'D' : 'D',
			'00' : 'O',
		}
		
		ctxt=""
		periodo_id = None
		n=0
		separator = '|'
		for recibo in self.browse(cr, uid, ids, context):
			if periodo_id != recibo.period_id.id and periodo_id is not None:
				raise osv.except_osv('Alerta','Hay periodos distintos en al consulta')
			periodo_id = recibo.period_id.id
			has_ret = '1' if recibo.has_retention else '0'
			com_type = parser[recibo.com_type]
			n = n+1

			ctxt += recibo.doc_type + separator
			ctxt += recibo.doc_number + separator
			ctxt += com_type + separator
			ctxt += recibo.serie + separator
			ctxt += recibo.numero + separator
			ctxt += str(recibo.amount) + separator
			ctxt += datetime.strptime(recibo.fechaemision, '%Y-%m-%d').strftime('%d/%m/%Y') + separator
			ctxt += datetime.strptime(recibo.fechapago, '%Y-%m-%d').strftime('%d/%m/%Y') + separator
			ctxt += has_ret + separator
			ctxt += separator
			ctxt += separator
			ctxt=ctxt+"""\r\n"""

		objperiodo = self.pool.get('account.period').browse(cr,uid,periodo_id,context)
		
		code = '0601'
		periodo = objperiodo.name.split('/')
		name = periodo[1]+periodo[0]
		user = self.pool.get('res.users').browse(cr,uid,uid,context)
		ruc = user.company_id.partner_id.doc_number
		file_name = code + name + ruc + '.4ta'
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		ruc_company= self.pool.get('res.users').browse(cr,uid,uid,context).company_id.partner_id.vat[2:]
		i = datetime.now()
		contenido ='0'
		if len(ctxt)>10:
			contenido ='1'
		vals = {
			'output_name': file_name,
			'output_file': base64.encodestring(self.eliminarAcentos(ctxt)),		
		}
		sfs_id = sfs_obj.create(cr, uid, vals, context=context)
		print 'sfs_id', sfs_id
		return sfs_id
	'''