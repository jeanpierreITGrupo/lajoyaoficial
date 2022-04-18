
# -*- coding: utf-8 -*-
# __openerp__.py
{
    'name':  "Productos: Reporte General",
    'category': 'Other',
    'author': 'ITGrupo',
    'depends': ['product'],
    'version': '1.0',
    'description': """
    Reporte Excel con los siguiente campos:
    Codigo,Unidad de Medida,Descripción,Tipo de Producto,Categoria interna,Cuenta de Gasto
    """,
    'data': [        
        'product_report_wizard_view.xml',
    ],
}
