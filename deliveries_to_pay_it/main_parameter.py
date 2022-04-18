# -*- coding: utf-8 -*-

from openerp import models, fields, api

class main_parameter(models.Model):
	_name = 'main.parameter'

	def init(self, cr):
		cr.execute('select id from res_users')
		uid = cr.dictfetchall()
		print 'uid', uid
		print 'uid0', uid[0]['id']
		cr.execute('select id from main_parameter')
		ids = cr.fetchall()
		
		print 'ids', ids
		
		if len(ids) == 0:
			cr.execute("""INSERT INTO main_parameter (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")
	
	name = fields.Char('Nombre',size=50, default='Parametros Generales')
	deliver_account_mn = fields.Many2one('account.account','Rendicion Moneda Nacional')
	deliver_account_me = fields.Many2one('account.account','Rendicion Moneda Extranjera')
	loan_account_mn = fields.Many2one('account.account','Cuenta Prestamos')
	loan_account_me = fields.Many2one('account.account','Cuenta Prestamos M.E.')
	loan_journal_mn = fields.Many2one('account.journal','Diario Rendiciones M.N.')
	loan_journal_me = fields.Many2one('account.journal','Diario Rendiciones M.E.')
	export_document_id = fields.Many2one('it.type.document', string="Documento de Exportacion",index=True)
	no_home_document_id = fields.Many2one('it.type.document', string="Comprobante de Pago No domiciliado",index=True)
	no_home_debit_document_id = fields.Many2one('it.type.document', string="N. Debito no domiciliado",index=True)
	no_home_credit_document_id = fields.Many2one('it.type.document', string="N. Credito no domiciliado",index=True)
	