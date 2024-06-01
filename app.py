from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
from azure.ai.formrecognizer import DocumentAnalysisClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Check if the uploads folder exists, if not, create it
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

endpoint = os.environ.get('endpoint')
key = os.environ.get('key')

document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    service = request.form.get('service-select')
    input_method = request.form.get('input-method')
    if service == 'Invoices':
        poller_method = 'prebuilt-invoice'
    elif service == 'Receipts':
        poller_method = 'prebuilt-receipt'
    elif service == 'Other Documents':
        poller_method = 'finance_insight_1'
    
    if input_method == 'file' and 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            with open(file_path, "rb") as fh:
                file_buf = BytesIO(fh.read())
            poller = document_analysis_client.begin_analyze_document(poller_method, file_buf)
    elif input_method == 'url':
        form_url = request.form.get('bill_url')
        if form_url:
            poller = document_analysis_client.begin_analyze_document_from_url(poller_method, form_url)
    else:
        return redirect(request.url)
    
    bill_data = poller.result()
    
    results = []
    if poller_method == 'prebuilt-invoice':
        for idx, invoice in enumerate(bill_data.documents):
            invoice_data = {}
            vendor_name = invoice.fields.get("VendorName")
            if vendor_name:
                invoice_data["Vendor Name"] = vendor_name.value
            
            vendor_address = invoice.fields.get("VendorAddress")
            if vendor_address:
                invoice_data["Vendor Address"] = vendor_address.value

            vendor_address_recipient = invoice.fields.get("VendorAddressRecipient")
            if vendor_address_recipient:
                invoice_data["Vendor Address Recipient"] = vendor_address_recipient.content

            customer_name = invoice.fields.get("CustomerName")
            if customer_name:
                invoice_data["Customer Name"] = customer_name.value

            customer_id = invoice.fields.get("CustomerId")
            if customer_id:
                invoice_data["Customer Id"] = customer_id.value

            customer_address = invoice.fields.get("CustomerAddress")
            if customer_address:
                invoice_data["Customer Address"] = customer_address.value

            customer_address_recipient = invoice.fields.get("CustomerAddressRecipient")
            if customer_address_recipient:
                invoice_data["Customer Address Recipient"] = customer_address_recipient.value

            invoice_id = invoice.fields.get("InvoiceId")
            if invoice_id:
                invoice_data["Invoice Id"] = invoice_id.value

            invoice_date = invoice.fields.get("InvoiceDate")
            if invoice_date:
                invoice_data["Invoice Date"] = invoice_date.value

            invoice_total = invoice.fields.get("InvoiceTotal")
            if invoice_total:
                invoice_data["Invoice Total"] = invoice_total.value

            billing_address = invoice.fields.get("BillingAddress")
            if billing_address:
                invoice_data["Billing Address"] = billing_address.value

            billing_address_rec = invoice.fields.get("BillingAddressRecipient")
            if billing_address_rec:
                invoice_data["Billing Address Recipient"] = billing_address_rec.value

        results.append(invoice_data)
    elif poller_method == 'prebuilt-receipt':
        for idx, receipt in enumerate(bill_data.documents):
            receipt_data = {}

            receipt_type = receipt.doc_type
            if receipt_type:
                receipt_data["Receipt Type"] = receipt_type

            merchant_name = receipt.fields.get("MerchantName")
            if merchant_name:
                receipt_data["Merchant Name"] = merchant_name.value

            transaction_date = receipt.fields.get("TransactionDate")
            if transaction_date:
                receipt_data["Transaction Date"] = transaction_date.value


            subtotal = receipt.fields.get("Subtotal")
            if subtotal:
                receipt_data["Subtotal"] = subtotal.value

            tax = receipt.fields.get("TotalTax")
            if tax:
                receipt_data["Tax"] = tax.value

            tip = receipt.fields.get("Tip")
            if tip:
                receipt_data["Tip"] = tip.value

            total = receipt.fields.get("Total")
            if total:
                receipt_data["Total"] = total.value

        results.append(receipt_data)
    elif poller_method == 'finance_insight_1':
        for idx, doc in enumerate(bill_data.documents):
            doc_data = {}

            doc_type = doc.fields.get('bill_type')
            if doc_type.value is not None:
                doc_data["Bill Type"] = doc_type.value

            po_date = doc.fields.get('po_date')
            if po_date.value is not None:
                doc_data["PO Date"] = po_date.value

            currency = doc.fields.get('currency')
            if currency.value is not None:
                doc_data["Currency"] = currency.value

            company_name = doc.fields.get('company_name')
            if company_name.value is not None:
                doc_data["Company Name"] = company_name.value

            invoice_no = doc.fields.get('invoice_no')
            if invoice_no.value is not None:
                doc_data["Invoice Number"] = invoice_no.value

            add_notes = doc.fields.get('add_notes')
            if add_notes.value is not None:
                doc_data["Additional Notes"] = add_notes.value

            invoice_date = doc.fields.get('invoice_date')
            if invoice_date.value is not None:
                doc_data["Invoice Date"] = invoice_date.value

            po_no = doc.fields.get('po_no')
            if po_no.value is not None:
                doc_data["PO Number"] = po_no.value

            tax = doc.fields.get('tax')
            if tax:
                doc_data["Tax"] = tax.value

            subtotal = doc.fields.get('subtotal')
            if subtotal:
                doc_data["Subtotal"] = subtotal.value

            po_vendor_ct = doc.fields.get('po_vendor_ct')
            if po_vendor_ct.value is not None:
                doc_data["PO Vendor Count"] = po_vendor_ct.value

            vendor_name = doc.fields.get('vendor_name')
            if vendor_name.value is not None:
                doc_data["Vendor Name"] = vendor_name.value

            vendor_address = doc.fields.get('vendor_address')
            if vendor_address.value is not None:
                doc_data["Vendor Address"] = vendor_address.value

            customer_name = doc.fields.get('customer_name')
            if customer_name.value is not None:
                doc_data["Customer Name"] = customer_name.value

            total = doc.fields.get('total')
            if total is not None:
                doc_data["Total"] = total.value

            customer_company = doc.fields.get('customer_company')
            if customer_company.value is not None:
                doc_data["Customer Company"] = customer_company.value

            doc_date = doc.fields.get('receipt_date')
            if doc_date.value is not None:
                doc_data["Receipt Date"] = doc_date.value

            receipt_id = doc.fields.get('receipt_id')
            if receipt_id.value is not None:
                doc_data["Receipt ID"] = receipt_id.value

            customer_address = doc.fields.get('customer_address')
            if customer_address.value is not None:
                doc_data["Customer Address"] = customer_address.value
        results.append(doc_data)

    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
