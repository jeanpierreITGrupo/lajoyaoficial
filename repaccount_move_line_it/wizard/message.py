from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

WARNING_TYPES = [('warning','Warning'),('info','Information'),('error','Error')]

class warning(osv.osv_memory):
    _name = 'warning'
    _description = 'warning'
    _columns = {
        'type': fields.selection(WARNING_TYPES, string='Type', readonly=True),
        'title': fields.char(string="Title", size=100, readonly=True),
        'message': fields.text(string="Message", readonly=True),
    }
    _req_name = 'title'

    def _get_view_id(self, cr, uid):
        """Get the view id
        @return: view id, or False if no view found
        """
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 
            'osc_integ', 'warning_form')
        return res and res[1] or False

    def message(self, cr, uid, context):
        print "hola"
        message = self.browse(cr, uid, id)
        print "hola",message
        res = {
            'name': message.title,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self._get_view_id(cr, uid),
            'res_model': 'warning',
            'domain': [],
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': message.id
        }
        return res

    def warning(self, cr, uid, title, message, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'warning'})
        res = self.message(cr, uid, id, context)
        return res

    def info(self, cr, uid, title, message, context=None):
        obj_id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'info'})
        res = self.message(cr, uid, obj_id, context)
        return res

    def error(self, cr, uid, title, message, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'error'})
        res = self.message(cr, uid, id, context)
        return res