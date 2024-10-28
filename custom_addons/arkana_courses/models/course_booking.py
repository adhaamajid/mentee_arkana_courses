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
                               # context_today = the active client's/ user timezone
                            default = lambda self: fields.Date.context_today(self))
    expiration_date = fields.Date('Expiration Date', 
                                default = lambda self: fields.Date.context_today(self) + timedelta(days=+7))
            # tracking untuk menuliskn perubahan di bawah/noted
    user_id = fields.Many2one('res.users', string='Salesperson', index = True, tracking = True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('canceled', 'Canceled')
    ], string='State', tracking = True, default = 'draft', index = True)

    def action_draft(self):
        self.state = 'draft'
    
    @api.model
    def cron_update_state(self):
        today = fields.Date.today()
        draft_records = self.search([('state', '=', 'draft'), ('expiration_date', '<=', today)])
        draft_records.write({'state' : 'canceled'})
        return True

    booking_line_ids = fields.One2many('course.booking.line', 'course_booking_id', string='Booking Line')
    # Monetary fields berkaitan dengan keuangan / currency -> laporan akhir
    price_total = fields.Monetary(compute='_compute_price_total', string='Price Total',
                                store = True, currency_field='currency_id')
    
    @api.depends('booking_line_ids', 'booking_line_ids.sale_price')
    #tidak selalu setiap kodisi, tapi akan ketrigger tanpa refresh
    def _compute_price_total(self):
        for rec in self:
            price_total = sum(rec.booking_line_ids.mapped('sale_price'))
            rec.price_total = price_total
            
    @api.model
    def create(self, vals):
        # Jika field 'name' kosong, generate sequence
        if vals.get('name', _('New')) == _('New'):
            # Gunakan sequence dengan code 'course.booking'
            vals['name'] = self.env['ir.sequence'].next_by_code('course.booking') or _('New')
        return super(CourseBooking, self).create(vals)


    sale_order_line_ids = fields.One2many('sale.order', 'course_booking_id', string='Sale Order Line')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sale Order Count')

    def action_confirm(self):
        for rec in self:
            existing_sale_orders = self.env['sale.order'].search([('course_booking_id', '=', rec.id)])

            if not existing_sale_orders or all(order.state not in ['draft', 'sale'] for order in existing_sale_orders):
                # Buat sale order baru jika tidak ada yang ada atau semua sudah dalam state selain draft dan sale
                rec.name = self.env['ir.sequence'].next_by_code('course.booking')
                rec._create_sale_order()
                rec.state = 'confirm'
            elif any(order.state == 'draft' for order in existing_sale_orders):
                # Jika ada sale order yang masih dalam state draft, update order tersebut
                for order in existing_sale_orders:
                    if order.state == 'draft':
                        order.write({
                            'partner_id': rec.partner_id.id,
                            'user_id': rec.user_id.id,
                            'validity_date': rec.expiration_date,
                            'course_booking_id': rec.id,
                            'order_line': [(5, 0, 0)] + rec._prepare_order_line(),  # Clear existing lines
                        })
                rec.state = 'confirm'
            else:
                raise ValidationError(_('Cannot confirm this booking as the related sale orders are not in the correct state.'))

        return True

    @api.depends('sale_order_line_ids')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_line_ids)
    
    def _create_sale_order(self):
        sale_order_obj = self.env['sale.order']
        sale_order_values = self._prepare_sale_order_values()
        sale_order_id = sale_order_obj.create(sale_order_values)
        return sale_order_id
        
    def _prepare_sale_order_values(self):
        return {
            'partner_id' : self.partner_id.id,
            'user_id' : self.user_id.id,
            'origin' : self.name,
            'validity_date' : self.expiration_date,
            'date_order' : fields.Datetime.now(),
            'course_booking_id' : self.id,
            'order_line' : self._prepare_order_line()
        }
    
    def _prepare_order_line(self):
        # order_line_values = []
        # for record in self.booking_line_ids:
        #     order_line_values.append((0, 0, {
        #         'course_booking_line_id' : record.id,
        #         'product_id' : record.product_id.id,
        #         'name' : '%s - %s' % (record.product_id.name, record.course_subject_id.name),
        #         'product_uom' : record.product_id.uom_id.id,
        #         'product_uom_qty' : 1,
        #         'price_unit' : record.sale_price
        #     }))
        values = [(0, 0, {
            'course_booking_line_id' : record.id,
            'product_id' : record.product_id.id,
            'name' : '%s - %s' % (record.product_id.name, record.course_subject_id.name),
            'product_uom' : record.product_id.uom_id.id,
            'product_uom_qty' : 1,
            'price_unit' : record.sale_price
        }) for record in self.booking_line_ids]
        return values
    
    def action_sale_order_view(self):
        action = self.env['ir.actions.act_window']._for_xml_id('sale.act_res_partner_2_sale_order')
        action["domain"] = [("course_booking_id", "in", self.ids)]
        action["context"] = {'create' : 0, 'edit' : 0}
        return action

    def action_cancel(self):
        existing_sale_orders = self.env['sale.order'].search([('course_booking_id', '=', self.id)])
    
        if any(order.state == 'sale' for order in existing_sale_orders):
            raise ValidationError(_('Tidak dapat membatalkan booking ini karena memiliki sale order yang sudah dikonfirmasi.'))

        self.write({'state': 'canceled'})

    def unlink(self):
        for record in self:
            # Cek apakah state bukan draft atau cancel
            if record.state not in ['draft', 'canceled']:
                raise ValidationError('You can only delete records in Draft or Cancelled state.')

            # Cek apakah ada sale order terkait yang belum dibatalkan
            existing_sale_orders = self.env['sale.order'].search([('course_booking_id', '=', record.id)])
            if existing_sale_orders and any(order.state != 'cancel' for order in existing_sale_orders):
                raise ValidationError('Tidak dapat menghapus booking ini karena memiliki sale order terkait yang belum dibatalkan.')
        
        return super(CourseBooking, self).unlink()

# CourseBookingLine remains unchanged
class CourseBookingLine(models.Model):
    _name = 'course.booking.line'
    _description = 'Course Booking Line'
    _rec_name = 'course_booking_id'
    
    course_booking_id = fields.Many2one('course.booking', string='Course Booking', index=True, 
                                         ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', index=True,
                                  store=True, related='course_booking_id.partner_id')
    booking_date = fields.Date('Booking Date', index=True, store=True, related='course_booking_id.booking_date')
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, store=True, related='course_booking_id.user_id')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                   related='course_booking_id.currency_id', store=True)
    product_id = fields.Many2one('product.product', string='Product', index=True,
                                  ondelete='restrict')

    course_subject_id = fields.Many2one('course.subject', string='Course Subject', index=True,
                                         ondelete='restrict', domain="[('id', 'in', course_subject_ids)]")
    course_subject_ids = fields.Many2many('course.subject', string='Course Subject', 
                                           compute='_get_course_subject_ids')
    reference = fields.Char('Reference', related='course_subject_id.reference')
    sale_price = fields.Monetary(compute='_compute_sale_price', string='Sale Price', store=True,
                                  currency_field='currency_id')
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True,
                                   ondelete='restrict', domain="[('id', 'in', employee_ids)]")
    employee_ids = fields.Many2many('hr.employee', string='Course Subject', 
                                     compute='_get_employee_ids')

    @api.depends('course_subject_id')
    def _compute_sale_price(self):
        for rec in self:
            rec.sale_price = rec.course_subject_id.sale_price if rec.course_subject_id else 0

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

