# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
import datetime


class account_voucher(models.Model):

    _inherit = 'account.voucher'

    # ,cr, uid, id, context=None

    def renew_license(self, cr, uid, id, context=None):

        query = """
        delete from account_move_line where id in (
        select ide_linea from (
        select id as ide_linea,debit,credit from account_move_line  where 
        move_id=(select move_id from account_voucher where id=%d)
        and debit=0
        and credit=0)tt)
        """ % id[0]

        a = cr.execute(query)
        # rows = cr.fetchall()

        print "llamada exitosa"
        print a
