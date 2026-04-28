import frappe
from frappe.utils import date_diff, fmt_money, formatdate, now_datetime
from frappe.utils.data import escape_html


RECIPIENTS = ["pratikshya.gochhayat@clapgrow.com", "ritika@clapgrow.com","beetashoke.chakraborty@clapgrow.com","accounts@clapgrow.com"]



def send_daily_payment_entry_email():
	"""Send Payment Entry rows submitted today (by custom_submitted_time) within the configured window."""
	rows = _get_payment_entry_rows_for_today_till_11_am()

	if not rows:
		return

	report_date = formatdate(now_datetime().date(), "dd-MM-yyyy")
	subject = f"Daily Payment Entry Report - {report_date}"
	body = _build_email_body(rows, report_date)

	frappe.sendmail(
		recipients=RECIPIENTS,
		subject=subject,
		message=body,
	)


def _get_payment_entry_rows_for_today_till_11_am():
	"""Fetch Payment Entries submitted today from 12:00 AM to 4:30 PM (testing window; use custom_submitted_time)."""
	return frappe.db.sql(
		"""
		SELECT
			pe.name AS payment_entry,
			pe.party_name,
			pe.posting_date AS received_date,
			pe.paid_amount,
			per.reference_name,
			si.posting_date AS sales_invoice_posting_date
		FROM `tabPayment Entry` pe
		INNER JOIN `tabPayment Entry Reference` per
			ON per.parent = pe.name
		LEFT JOIN `tabSales Invoice` si
			ON si.name = per.reference_name
		WHERE pe.docstatus = 1
		  AND pe.custom_submitted_time IS NOT NULL
		  AND DATE(pe.custom_submitted_time) = CURDATE()
		  AND TIME(pe.custom_submitted_time) >= '00:00:00'
		  AND TIME(pe.custom_submitted_time) <= '16:30:00'
		  AND IFNULL(per.reference_name, '') != ''
		  AND per.reference_doctype = 'Sales Invoice'
		ORDER BY pe.name, per.idx
		""",
		as_dict=True,
	)


def _build_email_body(rows, report_date_display):
	"""Build the HTML table body for payment entry rows."""
	table_rows_html = []
	total_amount = 0

	for row in rows:
		invoice_posting_date = (
			formatdate(row.sales_invoice_posting_date, "dd-MM-yyyy")
			if row.sales_invoice_posting_date
			else ""
		)
		received_date = formatdate(row.received_date, "dd-MM-yyyy") if row.received_date else ""
		due_days = (
			date_diff(row.received_date, row.sales_invoice_posting_date)
			if row.sales_invoice_posting_date and row.received_date
			else ""
		)
		amount = row.paid_amount or 0
		total_amount += amount

		table_rows_html.append(
			f"""
			<tr>
				<td style="padding:8px 10px;border:1px solid #cfcfcf;">{escape_html(row.party_name or "")}</td>
				<td style="padding:8px 10px;border:1px solid #cfcfcf;">{escape_html(row.reference_name or "")}</td>
				<td style="padding:8px 10px;border:1px solid #cfcfcf;">{invoice_posting_date}</td>
				<td style="padding:8px 10px;border:1px solid #cfcfcf;">{received_date}</td>
				<td style="padding:8px 10px;border:1px solid #cfcfcf;text-align:center;">{due_days}</td>
				<td style="padding:8px 10px;border:1px solid #cfcfcf;text-align:right;">{fmt_money(amount, currency='INR')}</td>
			</tr>
			"""
		)

	return f"""
	<div style="font-family:Arial, Helvetica, sans-serif;color:#1f2937;">
		<p>Dear Team,</p>
		<p>Please find below the daily Payment Entry report for <b>{report_date_display}</b>.</p>

		<h3 style="margin:16px 0 8px 0;">AXIS BANK</h3>
		<table style="border-collapse:collapse;width:100%;font-size:13px;">
			<thead>
				<tr style="background-color:#f4f6f8;">
					<th style="padding:9px 10px;border:1px solid #cfcfcf;text-align:left;">Particulars</th>
					<th style="padding:9px 10px;border:1px solid #cfcfcf;text-align:left;">Sales Invoice No.</th>
					<th style="padding:9px 10px;border:1px solid #cfcfcf;text-align:left;">Posting Date</th>
					<th style="padding:9px 10px;border:1px solid #cfcfcf;text-align:left;">Received Date</th>
					<th style="padding:9px 10px;border:1px solid #cfcfcf;text-align:center;">Due Days</th>
					<th style="padding:9px 10px;border:1px solid #cfcfcf;text-align:right;">Amount</th>
				</tr>
			</thead>
			<tbody>
				{''.join(table_rows_html)}
			</tbody>
			<tfoot>
				<tr style="font-weight:700;background-color:#fafafa;">
					<td colspan="5" style="padding:9px 10px;border:1px solid #cfcfcf;text-align:right;">Total</td>
					<td style="padding:9px 10px;border:1px solid #cfcfcf;text-align:right;">{fmt_money(total_amount, currency='INR')}</td>
				</tr>
			</tfoot>
		</table>

		<p style="margin-top:16px;">Regards,<br>Prakash Steel ERP</p>
	</div>
	"""
