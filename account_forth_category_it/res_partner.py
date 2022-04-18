# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
class res_partner(osv.osv):
	_name='res.partner'
	_inherit='res.partner'
	_columns={
		'is_resident' : fields.boolean('No Domiciliado'),
		'has_agree' : fields.boolean('Convenio Doble Imposicion'),
	}
	
	_defaults={
		'is_resident' : False,
		'has_agree' : False,
	}
	
res_partner()
