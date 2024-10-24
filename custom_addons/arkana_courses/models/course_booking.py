from odoo import _, api, fields, models
from datetime import timedelta
from odoo.exceptions import ValidationError

class CourseBooking(models.Model):
    _name = 'course.booking'
    _description = 'Course Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Course Number', index = 'trigram', default='New', copy = False)
    partner_id = fields.Many2one('res.partner', string='Partner', index = True,
                                domain=[('is_mentee', '=', True)], tracking = True)
    company_id = fields.Many2one('res.company', string='Company', default = lambda self:self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                related='company_id.currency_id', store = True)
    booking_date = fields.Date('Booking Date', tracking = True,
                            default = lambda self: fields.Date.context_today(self))
    expiration_date = fields.Date('Expiration Date', 
                                default = lambda self: fields.Date.context_today(self) + timedelta(days=+7))
    user_id = fields.Many2one('res.users', string='Salesperson', index = True, tracking = True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('canceled', 'Canceled')
    ], string='State', tracking = True, default = 'draft', index = True)
    booking_line_ids = fields.One2many('course.booking.line', 'course_booking_id', string='Booking Line')
    price_total = fields.Monetary(compute='_compute_price_total', string='Price Total',
                                store = True, currency_field='currency_id')
    
    @api.model
    def _auto_cancel_course_booking(self):
        today = fields.Date.context_today(self)
        course_order = self.search([('state', '=', 'draft'), ('expiration_date', '<=', today)])
        course_order.write({'state' : 'canceled'})
        return True
    
    @api.depends('booking_line_ids', 'booking_line_ids.sale_price')
    def _compute_price_total(self):
        for rec in self:
            price_total = sum(rec.booking_line_ids.mapped('sale_price'))
            rec.price_total = price_total
    
    def action_confirm(self):
        for rec in self:
            sequence_name = self.env['ir.sequence'].next_by_code('course.booking.number.sequence')
            rec.write({'name' : sequence_name, 'state' : 'confirm'})
        return True

    def action_set_to_draft(self):
        self.write({'state' : 'draft'})
        return True
    
    def action_cancel(self):
        self.write({'state' : 'canceled'})
            
class CourseBookingLine(models.Model):
    _name = 'course.booking.line'
    _description = 'Course Booking Line'
    _rec_name = 'course_booking_id'
    
    course_booking_id = fields.Many2one('course.booking', string='Course Booking', index = True, 
                                    ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', index = True,
                                store = True, related='course_booking_id.partner_id')
    booking_date = fields.Date('Booking Date', index = True, store = True, related='course_booking_id.booking_date')
    user_id = fields.Many2one('res.users', string='Salesperson', index = True, store = True, related='course_booking_id.user_id')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                related='course_booking_id.currency_id', store = True)
    product_id = fields.Many2one('product.product', string='Product', index = True,
                                ondelete='restrict')
    course_subject_id = fields.Many2one('course.subject', string='Course Subject', index = True,
                                    ondelete='restrict', domain="[('id', 'in', course_subject_ids)]")
    course_subject_ids = fields.Many2many('course.subject', string='Course Subject', 
                                        compute='_get_course_subject_ids')
    reference = fields.Char('Reference', related='course_subject_id.reference')
    sale_price = fields.Monetary(compute='_compute_sale_price', string='Sale Price', store = True,
                                currency_field='currency_id')
    employee_id = fields.Many2one('hr.employee', string='Employee', index = True,
                                ondelete='restrict', domain="[('id', 'in', employee_ids)]")
    employee_ids = fields.Many2many('hr.employee', string='Course Subject', 
                                        compute='_get_employee_ids')
    
    @api.depends('course_subject_id')
    def _compute_sale_price(self):
        for rec in self:
            sale_price = rec.course_subject_id.sale_price if rec.course_subject_id else 0
            rec.sale_price = sale_price
    
    @api.depends('product_id')
    def _get_course_subject_ids(self):
        for rec in self:
            domain = [('product_id', '=', rec.product_id.id)] if rec.product_id else []
            rec.course_subject_ids = self.env['course.subject'].search(domain)
    
    @api.depends('course_subject_id')
    def _get_employee_ids(self):
        for rec in self:
            domain = [('id', 'in', rec.course_subject_id.mapped('employee_ids.id'))] if rec.course_subject_id else []
            rec.employee_ids = self.env['hr.employee'].search(domain)
    