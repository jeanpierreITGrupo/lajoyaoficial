# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp     import models, fields, api
import base64
import codecs

class mrp_plantas(models.Model):
	_name = 'mrp.plantas'

	name           = fields.Char('Nombre', required=True)
	default_value  = fields.Boolean('Por Defecto')
	secuencia      = fields.Many2one('ir.sequence','Secuencia')