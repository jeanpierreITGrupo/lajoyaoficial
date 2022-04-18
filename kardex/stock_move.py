# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv

class stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'
    _columns={
        'invoice_id': fields.many2one('account.invoice','Factura'),
        'analitic_id': fields.many2one('account.analytic.account','Cta. Analitica'),
		'price_unit': fields.float('Unit Price', help="Technical field used to record the product cost set by the user during a picking confirmation (when costing method used is 'average price' or 'real'). Value given in company currency and in product uom.",digits=(12,6)),  # as it's a technical field, we intentionally don't provide the digits attribute
    }
