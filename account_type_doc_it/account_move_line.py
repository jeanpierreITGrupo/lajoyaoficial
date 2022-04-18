# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions , _


class account_move_line(models.Model):
	_inherit = 'account.move.line'
	type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",index=True,ondelete='restrict')
	nro_comprobante = fields.Char('Comprobante', size=30)


class account_move(models.Model):
	_inherit= 'account.move'


	@api.one
	@api.constrains('name','period_id','journal_id')
	def constrains_name_move_period_id_journal(self):		
		if self.name and self.name != '/' and self.name != '' and self.state!= 'draft':
			filtro = []
			filtro.append( ('period_id','=',self.period_id.id) )
			filtro.append( ('journal_id','=',self.journal_id.id) )
			filtro.append( ('id','!=',self.id) )

			m = self.env['account.move'].search( filtro )
			for elem in m:
				t = str(self.name).replace(' ','')
				t_t = t.split('-')
				r_t = ''
				pos = 0
				for t_elem in t_t:
					for t_char in t_elem:
						if t_char == '0':
							pos += 1
						else:
							r_t += t_elem[pos:] + '-'
							pos= 0
							break
				r_t = r_t[:-1]

				t = str(elem.name).replace(' ','')
				t_t = t.split('-')
				r_t2 = ''
				pos = 0
				for t_elem in t_t:
					for t_char in t_elem:
						if t_char == '0':
							pos += 1
						else:
							r_t2 += t_elem[pos:] + '-'
							pos= 0
							break
				r_t2 = r_t2[:-1]

				if r_t == r_t2:				
					raise exceptions.Warning(_("Ya existe ese número de voucher para el periodo y mes seleccionado."))