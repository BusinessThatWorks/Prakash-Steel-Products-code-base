app_name = "prakash_steel"
app_title = "Prakash Steel"
app_publisher = "Beetashoke Chakraborty"
app_description = "Prakash Steel Customizations"
app_email = "beetashoke.chakraborty@clapgrow.com"
app_license = "mit"

# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------

fixtures = [
    {"doctype": "Custom Field", "filters": {"module": "Prakash Steel"}},
]

# ------------------------------------------------------------------------------
# DocType JavaScript
# ------------------------------------------------------------------------------

doctype_js = {
    "Material Request": "public/js/material_request.js",
    "Sales Order": "public/js/sales_order.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Item": "public/js/item.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Purchase Receipt": "public/js/purchase_receipt.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Production Plan": "public/js/production_plan.js",
    "Payment Reconciliation": "public/js/payment_reconciliation.js",
}

# ------------------------------------------------------------------------------
# Page JavaScript
# ------------------------------------------------------------------------------

page_js = {
    "procurement-tracker-dashboard": "prakash_steel/page/procurement_tracker_dashboard/procurement_tracker_dashboard.js",
    "sales-summary-dashboard": "prakash_steel/page/sales_summary_dashboard/sales_summary_dashboard.js",
    "item-insight-dashboard": "prakash_steel/page/item_insight_dashboard/item_insight_dashboard.js",
    "production-dashboard": "prakash_steel/page/production_dashboard/production_dashboard.js",
}

# ------------------------------------------------------------------------------
# App Include JS
# ------------------------------------------------------------------------------

app_include_js = [
    "/assets/prakash_steel/js/number_cards_uom.js"
]

# ------------------------------------------------------------------------------
# Document Events
# ------------------------------------------------------------------------------

doc_events = {

    "Item": {
        "validate": "prakash_steel.utils.item.validate_min_order_qty_and_batch_size",
        "on_update": "prakash_steel.utils.item.update_decoupled_lead_time_on_item_save",
    },

    "BOM": {
        "on_submit": "prakash_steel.utils.item.update_decoupled_lead_time_on_bom_save",
        "on_update_after_submit": "prakash_steel.utils.item.update_decoupled_lead_time_on_bom_save",
    },

    "Purchase Receipt": {
        "on_submit": "prakash_steel.utils.purchase_receipt.validate_purchase_receipt_quantity",
        "before_cancel": "prakash_steel.utils.purchase_receipt_cancel.validate_cancel_reason",
    },

    "Production Plan": {
        "on_submit": "prakash_steel.prakash_steel.utils.production_plan.on_production_plan_submit",
    },

    "Sales Order": {
        "before_cancel": "prakash_steel.utils.sales_order_cancel.validate_cancel_reason",
    },

    "Purchase Order": {
        "before_cancel": "prakash_steel.utils.purchase_order_cancel.validate_cancel_reason",
    },

    "Purchase Invoice": {
        "before_cancel": "prakash_steel.utils.purchase_invoice_cancel.validate_cancel_reason",
    },

    "Material Request": {
        "before_cancel": "prakash_steel.utils.material_request_cancel.validate_cancel_reason",
    },
}

# ------------------------------------------------------------------------------
# Scheduler Events
# ------------------------------------------------------------------------------

scheduler_events = {

    "cron": {
        # Runs daily at 14:52 server time
        "52 14 * * *": [
            "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.save_daily_on_hand_colour"
        ]
    },
}

# ------------------------------------------------------------------------------
# Override DocType Classes
# ------------------------------------------------------------------------------

override_doctype_class = {
    "Stock Entry": "prakash_steel.overrides.stock_entry.CustomStockEntry",
    "Payment Reconciliation": "prakash_steel.overrides.payment_reconciliation.CustomPaymentReconciliation",
    "Sales Invoice": "prakash_steel.overrides.sales_invoice.CustomSalesInvoice",
}