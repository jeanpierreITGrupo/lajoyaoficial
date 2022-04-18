# -*- encoding: utf-8 -*-
{
	'name'        : 'CATEGORIAS DE RUMA IT',
	'category'    : 'ruma',
	'author'      : 'ITGrupo',
	'depends'     : ['build_ruma_joya'],
	'version'     : '1.0',
	'description' :"""
		Agraga campo de categoría en ruma.
	""",
	'auto_install': False,
	'demo'        : [],
	'data'        :	['security/ir.model.access',
					 'mrp_plantas_data.xml',
					 'mrp_plantas_view.xml',
					 'armado_ruma_view.xml'],
	'installable' : True
}
