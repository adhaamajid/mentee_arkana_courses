from odoo import _, api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    course_booking_id = fields.Many2one('course.booking', string='Course Booking',
                                    index = True, copy = False)
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    course_booking_line_id = fields.Many2one('course.booking.line', string='Course Booking Line',
                                            index = True, copy = False)
