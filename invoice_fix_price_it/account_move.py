# -*- coding: utf-8 -*-
import pprint
import itertools
import openerp.addons.decimal_precision as dp

from lxml import etree

from openerp.osv import osv
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare


class account_move_line(models.Model):
	_inherit = "account.move.line"	
	
	location_id = fields.Many2one('stock.location', 'Ubicacion')
	