# -*- coding: utf-8 -*-
import logging
from odoo import fields, http, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.osv.expression import AND, OR
_logger = logging.getLogger(__name__)

from itertools import groupby
from operator import itemgetter

import pdfkit
import base64
import locale
locale.setlocale(locale.LC_ALL, 'en_US.utf8')
import os
from reportlab.lib.pagesizes import A4,A3,landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from odoo.http import request
import io
import csv



class PartnerLedgerController(portal.CustomerPortal):
    _items_per_page = 80
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner=request.env.user.partner_id
        values['client_count']=request.env['account.move.line'].sudo().search_count([('parent_state', '=', 'posted'),('partner_id','=',partner.id),('account_id.account_type', '=', 'asset_receivable'),('journal_id.type', 'not in',['Divers', 'general'])])

        return values

    def _prepare_portal_layout_values(self):
        """Values for /my/* templates rendering.

        Does not include the record counts.
        """
        # get customer sales rep
        sales_user_sudo = request.env['res.users']
        partner_sudo = request.env.user.partner_id
        if partner_sudo.user_id and not partner_sudo.user_id._is_public():
            sales_user_sudo = partner_sudo.user_id

        return {
            'sales_user': sales_user_sudo,
            'page_name': 'home',
        }

    def _get_searchbar_groupby_client(self):
        return {
            'none': {'input': 'none', 'label': _('none')},
            'date': {'input': 'date', 'label': _('Date')},
        }

    def _prepare_sale_portal_rendering_values_client(self, page=1, date_begin=None, date_end=None, sortby=None,search=None, search_in='all',groupby='none',quotation_page=False, **kwargs):
        #_logger.info("\n\n _prepare_sale_portal_rendering_values_client CALLED \n\n")
        partner_ledger = request.env['account.move.line']

        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()
        url = "/my/client"
        domain = [('parent_state', '=', 'posted'),('partner_id','=',partner.id),('account_id.account_type', '=', 'asset_receivable'),('journal_id.type', 'not in', ['Divers','general'])]
        searchbar_inputs = {
            'date': {'input': 'date', 'label': _('Search in Date')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        if search and search_in:
            search_domain = []
            if search_in == "from_to":
                try:
                    search_domain = [('date', '>=', date_begin), ('date', '<=', date_end)]
                    domain += search_domain
                except:
                    domain = domain
            else:
                try:
                    search_domain = OR([search_domain, [('date', '=', search)]])
                    domain += search_domain
                except:
                    domain = domain

        pager_values = portal_pager(
            url=url,
            total=partner_ledger.sudo().search_count(domain),
            page=page,
            step=80,
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby,'search_in': search_in,'search': search,},
        )

        lines = request.env['account.move.line'].sudo().search(domain, limit=80,offset=pager_values['offset'])
        lines_total = request.env['account.move.line'].sudo().search(domain,order='date asc, move_name asc, id')
        sorted_list=[]
        sort_credit = []
        d={}
        curruncies=request.env['res.currency'].sudo().search([('active','=','True')])
        for i in lines_total: 
            dic_credit = {
                'currency': i.currency_id.name,
                'date': i.date,
                'ref': i.move_name,
                'debit': locale.format_string("%.2f", abs(i.amount_currency), grouping=True) if i.amount_currency > 0 else 's',
                'credit': locale.format_string("%.2f", abs(i.amount_currency), grouping=True) if i.amount_currency < 0 else 's',
                'type': 'PAIEMENT' if i.journal_id.type == 'bank' else 'FACTURE',
                'credit1': i.amount_currency,
            }
            sort_credit.append(dic_credit)

        for item in sort_credit:
            d.setdefault(item['currency'], []).append(item)

        outputList = list(d.values())
        pValues = [[{'currency':d["currency"],'date':d["date"],
                     'date': d["date"],
                     'ref': d["ref"],
                     'debit': d["debit"],
                     'credit': d["credit"],
                     'type': d["type"],
                     'credit1': d["credit1"],} for d in row] for row in outputList]
        balance=[]
        test=['#CCFFCC','#FFB266','#FF99CC','#3399FF']
        all_colors=[]
        for j in range(0,len(pValues)):
            for i in range(0,len(test)):
                if j==i:
                    all_colors.append(test[i])
     
        colors=[]

        for j in range(0,len(pValues)):
            solde = 0
            for i in range(0,len(all_colors)):
               if j==i:
                for x in pValues[j]:
                    solde += x['credit1']
                    balance.append(solde)
                    colors.append(all_colors[i])
        print(balance)
        for i in pValues:
            for j in i:
              sorted_list.append(j)

        K = "sold"
        kk = "color"
        for dic, lis in zip(sorted_list, balance):
            print(lis)
            dic[K] = locale.format_string("%.2f", lis, grouping=True)
        for dic, lis in zip(sorted_list, colors):
            dic[kk] = lis

        debit_list = sorted(sorted_list, key=lambda x: x['date'])

        total=[]

        for i in request.env['account.move.line'].sudo().read_group([('parent_state', '=', 'posted'),
                                                                     ('partner_id', '=', partner.id),
                                                                     ('account_id.account_type', '=', 'asset_receivable')],
                                                                    ['debit:sum', 'credit:sum', 'balance:sum'], ['partner_id']):

            dic={'total': request.env['res.partner'].sudo().browse(i['partner_id'][0]).name+' TOTAL',
                'inv':'',
                'credit_total': locale.format_string("%.2f", i['credit'], grouping=True) + " " + request.env.company.currency_id.symbol,
                'debit_total': locale.format_string("%.2f", i['debit'], grouping=True) + " " + request.env.company.currency_id.symbol,
                'balance_total': locale.format_string("%.2f", i['balance'], grouping=True) + " " + request.env.company.currency_id.symbol,
                 'currency': request.env.company.currency_id.name}
            total.append(dic)

        values.update({
            'date': date_begin,
            'clients': lines_total.sudo(),
            'debit_list': debit_list,
            'curr': curruncies,
            'page_name': 'client',
            'total':total,
            'search_in': search_in,
            'search': search,
            'pager': pager_values,
            'default_url': url,
            'searchbar_inputs': searchbar_inputs,
        })
        print(values)
        return values


    def prepare_rows_data(self):
        headers = ["Date", "Référence", "Libellé", "Débit CNY", "Crédit CNY", "Solde CNY","Débit DZD", "Crédit DZD", "Solde DZD", "Débit EUR", "Crédit EUR", "Solde EUR","Débit USD", "Crédit USD", "Solde USD"]
        data = [headers]
        values = self._prepare_sale_portal_rendering_values_client()
        for entry in values["total"]:
            name = entry.get("total")
            credit_total = entry.get("credit_total")
            debit_total = entry.get("debit_total")
            balance_total = entry.get("balance_total")
            inv = entry.get("inv")
            row = [name, inv, inv, debit_total, credit_total, balance_total]
            data.append(row)

       
        for entry in values["debit_list"]:
            date = entry.get("date")
            ref = entry.get("ref")
            libelle = entry.get("type")
            
            debit_cny = credit_cny = solde_cny = ""
            debit_dzd = credit_dzd = solde_dzd = ""
            debit_eur = credit_eur = solde_eur = "" 
            debit_usd = credit_usd = solde_usd = "" 

            currency = entry.get("currency")
            if currency == "CNY":
                debit_cny = str(entry.get("debit")) + request.env.company.currency_id.symbol if entry.get("debit") != "s" else ""
                credit_cny = str(entry.get("credit")) + request.env.company.currency_id.symbol if entry.get("credit") != "s" else ""
                solde_cny = str(entry.get("sold")) + request.env.company.currency_id.symbol
            elif currency == "DZD":
                debit_dzd = str(entry.get("debit")) + "DA" if entry.get("debit") != "s" else ""
                credit_dzd = str(entry.get("credit")) + "DA" if entry.get("credit") != "s" else ""
                solde_dzd = str(entry.get("sold")) + "DA"
            elif currency == "EUR":
                debit_eur = str(entry.get("debit")) + "€" if entry.get("debit") != "s" else ""
                credit_eur = str(entry.get("credit")) + "€" if entry.get("credit") != "s" else ""
                solde_eur = str(entry.get("sold")) + "€"
            elif currency == "USD":
                debit_usd = str(entry.get("debit")) + "$" if entry.get("debit") != "s" else ""
                credit_usd = str(entry.get("credit")) + "$" if entry.get("credit") != "s" else ""
                solde_usd = str(entry.get("sold")) + "$"

            row = [date, ref, libelle, debit_cny, credit_cny, solde_cny, debit_dzd, credit_dzd, solde_dzd, debit_eur, credit_eur, solde_eur, debit_usd, credit_usd, solde_usd]
            data.append(row)

        return data

    def generate_pdf_file(self):
        data = self.prepare_rows_data()
        pdf_filename = "/tmp/generated.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=landscape(A3))
        elements = []
        table = Table(data)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),  # Gray background for the first row
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Text color for the first row
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center-align all cells
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Middle-align all cells
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),  # Inner grid lines
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),  # Border around the table
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),  # Gray background for the first row
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),  # Change font to Helvetica-Bold
            ('FONTSIZE', (0, 0), (-1, -1), 11),
        ])
        table.setStyle(table_style)
        title_text = "Rapport Solde Client"
        title_style = getSampleStyleSheet()["Title"]
        title = Paragraph(title_text, title_style)
        elements.append(title)
        elements.append(table)
        doc.build(elements)
        return pdf_filename
    
    @http.route(['/my/client', '/my/client/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_client(self, **kwargs): 
        values = self._prepare_sale_portal_rendering_values_client(quotation_page=True, **kwargs)
        _logger.info("\n\n ----------------- Values -----------------\n")
        _logger.info(values)
        _logger.info("\n\n------------------------------------------\n\n")
        return request.render("portal-client.portal_my_client", values)

    @http.route(['/my/client/generate_pdf'], type='json', auth="user")
    def generate_pdf(self, **kwargs):
        pdf_filename = self.generate_pdf_file()
        with open(pdf_filename, 'rb') as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
        return {'pdf_content': pdf_base64}

    @http.route(['/my/client/generate_excel'], type='json', auth="user")
    def generate_excel(self, **kwargs):
        data = self.prepare_rows_data()
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer) 
        for row in data:
            csv_writer.writerow(row)
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()
        return {'excel_content': csv_content}

class PaymentController(portal.CustomerPortal):
    _items_per_page = 80

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        values['payment_count'] = request.env['account.payment'].sudo().search_count([('partner_id','=',partner.id)])
        return values


    def _prepare_portal_layout_values(self):
        """Values for /my/* templates rendering.

        Does not include the record counts.
        """
        # get customer sales rep
        sales_user_sudo = request.env['res.users']
        partner_sudo = request.env.user.partner_id
        if partner_sudo.user_id and not partner_sudo.user_id._is_public():
            sales_user_sudo = partner_sudo.user_id

        return {
            'sales_user': sales_user_sudo,
            'page_name': 'home',
        }

    def _prepare_sale_portal_rendering_values_payment(
            self, page=1, date_begin=None, date_end=None, sortby=None, quotation_page=False, **kwargs
    ):
        account_payment = request.env['account.payment']

        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()

        url = "/my/payment"
        domain = [('partner_id','=',partner.id)]

        pager_values = portal_pager(
            url=url,
            total=account_payment.sudo().search_count(domain),
            page=page,
            step=80,
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
        )
        account_payments = request.env['account.payment'].sudo().search(domain, limit=80,
                                                         offset=pager_values['offset'])


        values.update({
            'date': date_begin,
            'payments': account_payments,
            'page_name': 'payment',
            'pager': pager_values,
            'default_url': url,

        })

        return values

    @http.route(['/my/payment','/my/payment/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payment(self, **kwargs):
        values = self._prepare_sale_portal_rendering_values_payment(quotation_page=True, **kwargs)
        return request.render("portal-client.portal_my_payment", values)
