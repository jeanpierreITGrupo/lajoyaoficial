# -*- coding: utf-8 -*-

from openerp import models, fields, api , exceptions , _

class account_move_line(models.Model):
	_inherit = 'account.move.line'
	
	nro_comprobante = fields.Char('Nro. Comprobante',size=30,copy=True)

class account_move(models.Model):
	_inherit = 'account.move'

	@api.one
	@api.constrains('ref')
	def constrains_nro_comprobante_it(self):
		if self.ref and self.journal_id.id and self.journal_id.type == 'bank' :
			filtro = []
			filtro.append( ('id','!=',self.id) )
			filtro.append( ('ref','=',self.ref) )
			filtro.append( ('journal_id','=',self.journal_id.id) )
			m = self.env['account.move'].search( filtro )
			if len(m)>0:
				raise exceptions.Warning( u"Número de Cheque Duplicado ("+self.ref+u").")



			"""class account_move(models.Model):
	_inherit = 'account.move'
	

	@api.one
	@api.constrains('ref')
	def constrains_ref_it(self):
		if self.ref and self.journal_id.id and self.journal_id.type == 'bank':
			filtro = []
			filtro.append( ('id','!=',self.id) )
			filtro.append( ('ref','=',self.ref) )
			if self.journal_id:
				filtro.append( ('journal_id','=', self.journal_id.id) )
			m = self.env['account.move'].search( filtro )
			if len(m)>0:
				raise exceptions.Warning(_("Número de Cheque Duplicado ("+self.ref+").")) """

