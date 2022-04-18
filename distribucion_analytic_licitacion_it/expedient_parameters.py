# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class purchase_requisition_line(models.Model):
	_inherit ='purchase.requisition.line'

	analytics_id = fields.Many2one('account.analytic.plan.instance','Distribución Analítica')

class purchase_requisition(models.Model):
	_inherit ='purchase.requisition'

	def _prepare_purchase_order_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
		t = super(purchase_requisition,self)._prepare_purchase_order_line(cr, uid, requisition, requisition_line, purchase_id, supplier, context)
		t['analytics_id']= requisition_line.analytics_id.id
		return t