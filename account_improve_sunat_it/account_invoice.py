# -*- coding: utf-8 -*-

from openerp import models, fields, api ,  _

class account_invoice(models.Model):
	_inherit = 'account.invoice'
	date = fields.Date('Fecha')
	voucher_number = fields.Char('Número de Comprobante',size=30)
	code_operation= fields.Char('Codigo de Operación',size=50)
	amount = fields.Float('Monto', digits=(12,2))
	account_ids = fields.One2many('account.perception','father_invoice_id',string='Documentos Relacionados')
	vacio = fields.Char('Vacio',size=30)

	tipo_tasa_percepcion = fields.Char('Tipo Tasa')
	numero_serie = fields.Char(u'Número de Documento')

	def copy(self, cr, uid, id, default=None, context=None):
		default['date']= None
		default['voucher_number']= None
		default['code_operation']= None
		default['amount']= None
		default['account_ids']= None
		return super(account_invoice,self).copy( cr, uid, id, default, context)

	@api.multi
	def name_get(self):
		context = self.env.context
		print context
		if context is None:
			context = {}
		
		TYPES = {
			'out_invoice': _('Invoice'),
			'in_invoice': _('Supplier Invoice'),
			'out_refund': _('Refund'),
			'in_refund': _('Supplier Refund'),
		}
		result = []
		for inv in self:
			comprobante = inv.supplier_invoice_number or ''
			if 'compro_name' in context:
				result.append((inv.id, comprobante))
			else:
				result.append((inv.id, "%s %s" % (inv.number or TYPES[inv.type], inv.name or '')))
		return result

class account_perception(models.Model):
	_name='account.perception'

	father_invoice_id = fields.Many2one('account.invoice',string="Factura")
	comprobante = fields.Char('Comprobante' ,size=50)
	tipo_doc = fields.Many2one('it.type.document',string="T.D.",ondelete='restrict')
	fecha = fields.Date('Fecha Emisión')
	perception = fields.Float('Total', digits=(12,2))
	base_imponible = fields.Float('Base Imponible',digits=(12,2))
	igv = fields.Float('IGV',digits=(12,2))