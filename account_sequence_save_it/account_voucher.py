# -*- coding: utf-8 -*-

import time
from lxml import etree

from openerp import models, fields, api
from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp


class account_voucher(models.Model):
	_inherit = 'account.voucher'

	@api.one
	def unlink(self):
		if self.number and self.number != '':
			raise osv.except_osv('Alerta!', "No se puede eliminar un Pago ya asentado anteriormente.")
		return super(account_voucher,self).unlink()