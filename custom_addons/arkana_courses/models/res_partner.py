from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    citizen = fields.Selection([('WNA', 'WNA'), ('WNI', 'WNI')], string="Citizen")
    registration_number = fields.Char(string="Registration Number")
    is_mentee = fields.Boolean(string="Is Mentee", default=False)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    dob = fields.Date(string="Date of Birth")
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    join_date = fields.Date(string="Join Date")

    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                record.age = fields.Date.today().year - record.dob.year
            else:
                record.age = 0

    def mark_as_student(self):
        for partner in self:
            if partner.is_company:
                raise UserError("Cannot mark a company as student.")
            partner.write({
                'is_mentee': True,
                'join_date': fields.Date.today(),
                'registration_number': self.env['ir.sequence'].next_by_code('res.partner.student'),
            })

    _sql_constraints = [
        ('email_unique', 'unique(email)', 'Email must be unique!'),
        ('phone_unique', 'unique(phone)', 'Phone must be unique!')
    ]

    @api.model
    def create(self, vals):
        if vals.get('is_mentee'):
            # Ambil citizen dari vals, jika tidak ada atau nilainya False, gunakan 'OTHER'
            citizen_code = vals.get('citizen') or 'OTHER'
            
            # Generate sequence untuk registration_number
            registration_sequence = self.env['ir.sequence'].next_by_code('res.partner.mentee') or '/'
            
            # Buat registration_number dengan format sesuai citizen
            vals['registration_number'] = f"{citizen_code}-{registration_sequence}"
        
        return super(ResPartner, self).create(vals)


    def write(self, vals):
        for record in self:
            if 'citizen' in vals and record.is_mentee:
                # Ambil citizen baru, jika tidak ada atau nilainya False, gunakan 'OTHER'
                new_citizen = vals.get('citizen') or 'OTHER'
                
                # Cek apakah registration_number sudah diisi, jika tidak, buat baru
                if record.registration_number:
                    # Pisahkan registration_number untuk mengganti bagian citizen saja
                    reg_parts = record.registration_number.split('-')
                    # Update hanya bagian citizen dari registration_number
                    vals['registration_number'] = f"{new_citizen}-{reg_parts[2]}"
                else:
                    # Jika belum ada registration_number, buat baru
                    registration_sequence = self.env['ir.sequence'].next_by_code('res.partner.mentee') or '/'
                    vals['registration_number'] = f"{new_citizen}-{registration_sequence}"
            
            return super(ResPartner, self).write(vals)
    
    # @api.onchange('dob')
    # def _onchange_dob(self):
    #     for rec in self:
    #         if rec.dob:
    #             rec.join_date = rec.dob
        


