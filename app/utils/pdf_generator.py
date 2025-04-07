from fpdf import FPDF
from PIL import Image
import os
import sys

class ReceiptPDF(FPDF):
    def __init__(self, payment, fine, base_path):
        super().__init__()
        self.payment = payment
        self.fine = fine
        self.base_path = base_path
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Digital Justice System', 0, 1, 'C')
        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'Government of India', 0, 1, 'C')
        self.ln(20)

    def content(self):
        # Receipt Details
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Receipt Details', 0, 1)
        self.set_font('Arial', '', 12)
        
        self.cell(90, 10, f'Receipt Number: {self.payment.receipt_number}', 0, 0)
        self.cell(0, 10, f'Payment Date: {self.payment.payment_date.strftime("%d %B %Y, %H:%M")}', 0, 1)
        self.cell(90, 10, f'Transaction ID: {self.payment.transaction_id}', 0, 0)
        self.cell(0, 10, f'Payment Method: {self.payment.payment_method}', 0, 1)
        self.ln(10)

        # Fine Details
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Fine Details', 0, 1)
        self.set_font('Arial', '', 12)
        
        self.cell(90, 10, f'Challan Number: {self.fine.challan_number}', 0, 0)
        self.cell(0, 10, f'Violation Type: {self.fine.violation_type}', 0, 1)
        self.cell(90, 10, f'Violation Date: {self.fine.violation_date.strftime("%d %B %Y")}', 0, 0)
        self.cell(0, 10, f'Issued By: Officer ID {self.fine.issued_by}', 0, 1)
        self.ln(10)

        # Payment Summary
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Payment Summary', 0, 1)
        self.set_font('Arial', '', 12)
        
        self.cell(90, 10, f'Fine Amount: ₹{self.fine.amount}', 0, 0)
        if self.payment.fine.calculate_penalty() > 0:
            self.cell(0, 10, f'Late Penalty: ₹{self.payment.fine.calculate_penalty()}', 0, 1)
            self.cell(0, 10, 'Total Amount Paid: ₹{:.2f}'.format(
                self.fine.amount + self.payment.fine.calculate_penalty()), 0, 1)
        else:
            self.cell(0, 10, 'Total Amount Paid: ₹{:.2f}'.format(self.fine.amount), 0, 1)
        self.ln(10)

        # QR Code
        try:
            qr_path = os.path.join(self.base_path, 'static', 'uploads', 'qrcodes', f'receipt_{self.payment.id}.png')
            if os.path.exists(qr_path):
                self.image(qr_path, x=150, y=170, w=40)
        except:
            pass

def generate_receipt_pdf(payment, fine, output_path):
    # Get the base path from the output path
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(output_path)))
    
    # Create PDF
    pdf = ReceiptPDF(payment, fine, base_path)
    pdf.output(output_path)
