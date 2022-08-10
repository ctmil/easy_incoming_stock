from odoo import tools, models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def btn_create_move_lines(self):
        self.ensure_one()
        if self.state not in ['draft','assigned']:
            raise ValidationError('No se puede procesar un ingreso en este estado')
        lines_text = self.lines_text
        lines = lines_text.split('\n')
        for line in lines:
            items = line.split(',')
            default_code = items[0]
            serial_number = items[1]
            product_id = self.env['product.product'].search([('default_code','=',default_code)],limit=1)
            if not product_id:
                raise ValidationError('El producto %s no esta presente'%(default_code))
            if product_id.tracking != 'serial':
                raise ValidationError('El producto no esta configurado para procesar nros de serie')
            lot_id = self.env['stock.production.lot'].search([('product_id','=',product_id.id),('name','=',serial_number)])
            if lot_id:
                raise ValidationError('El nro de serie %s para el producto %s esta presente'%(serial_number,default_code))
            vals_lot = {
                    'product_id': product_id.id,
                    'name': serial_number,
                    'ref': serial_number,
                    }
            lot_id = self.env['stock.production.lot'].create(vals_lot)
            move_id = self.env['stock.move'].search([('picking_id','=',self.id),('product_id','=',product_id.id)])
            if not move_id:
                raise ValidationError('Esta transferencia no va a procesar el producto %s'%(default_code))
            vals = {
                    'move_id': move_id.id,
                    'product_id': product_id.id,
                    'product_uom_id': product_id.uom_id.id,
                    'lot_id': lot_id.id,
                    'location_id': move_id.location_id.id,
                    'location_dest_id': move_id.location_dest_id.id,
                    'is_inventory': True,
                    'picking_id': self.id,
                    'state': move_id.state,
                    'lot_name': lot_id.ref,
                    'origin': self.origin,
                    'picking_partner_id': self.partner_id.id,
                    'qty_done': 1,
                    }
            picking_id = self.env['stock.move.line'].create(vals)

    lines_text = fields.Text('Lineas a procesar')
