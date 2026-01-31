// Copyright (c) 2025, Prakash Steel and contributors
// For license information, please see license.txt

// Ensure the page is registered before adding event handlers
if (!frappe.pages['item-insight-dashboard']) {
	frappe.pages['item-insight-dashboard'] = {};
}

frappe.pages['item-insight-dashboard'].on_page_load = function (wrapper) {
	console.log('Item Insight Dashboard page loading...');

	// Build page shell
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Item Insight Dashboard'),
		single_column: true,
	});

	// Add custom CSS for fixed table, scrollbar, and sticky columns
	$('<style>')
		.prop('type', 'text/css')
		.html(`
			.item-insight-table-wrapper {
				width: 100%;
				max-width: 100%;
				height: calc(100vh - 100px);
				overflow: auto;
				position: relative;
			}
			.item-insight-table-wrapper::-webkit-scrollbar {
				width: 12px;
				height: 12px;
			}
			.item-insight-table-wrapper::-webkit-scrollbar-track {
				background: #f1f1f1;
				border-radius: 6px;
			}
			.item-insight-table-wrapper::-webkit-scrollbar-thumb {
				background: #888;
				border-radius: 6px;
			}
			.item-insight-table-wrapper::-webkit-scrollbar-thumb:hover {
				background: #555;
			}
			.item-insight-table {
				position: relative;
			}
			.item-insight-table thead {
				position: sticky;
				top: 0;
				z-index: 100;
			}
			.item-insight-table thead th {
				position: sticky;
				top: 0;
			}
		`)
		.appendTo('head');

	// Initialize dashboard state
	const state = {
		page,
		wrapper,
		filters: {},
		controls: {},
		expandedRows: new Set() // Track expanded rows for warehouse stock
	};

	// Initialize dashboard components
	initializeDashboard(state);
};

frappe.pages['item-insight-dashboard'].on_page_show = function () {
	console.log('Item Insight Dashboard shown');
};

function initializeDashboard(state) {
	// Clear main content
	state.page.main.empty();

	// Create filter bar
	createFilterBar(state);

	// Create table container
	createTableContainer(state);

	// Set default values
	setDefaultFilters(state);

	// Bind event handlers
	bindEventHandlers(state);

	// Load initial data
	refreshDashboard(state);
}

function createFilterBar(state) {
	// Main filter container
	const $filterBar = $('<div class="item-insight-filters" style="display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin-bottom:16px;justify-content:space-between;background:#f8f9fa;padding:16px;border-radius:8px;"></div>');

	// Filter controls container
	const $filterControls = $('<div style="display:flex;gap:12px;align-items:end;flex-wrap:wrap;"></div>');

	// Individual filter wrappers
	const $fromWrap = $('<div style="min-width:200px;"></div>');
	const $toWrap = $('<div style="min-width:200px;"></div>');
	const $itemWrap = $('<div style="min-width:220px;"></div>');
	const $btnWrap = $('<div style="display:flex;align-items:end;gap:8px;"></div>');

	// Assemble filter controls
	$filterControls.append($fromWrap).append($toWrap).append($itemWrap);
	$filterBar.append($filterControls).append($btnWrap);
	$(state.page.main).append($filterBar);

	// Create filter controls
	createFilterControls(state, $fromWrap, $toWrap, $itemWrap, $btnWrap);
}

function createFilterControls(state, $fromWrap, $toWrap, $itemWrap, $btnWrap) {
	// Date controls
	state.controls.from_date = frappe.ui.form.make_control({
		parent: $fromWrap.get(0),
		df: {
			fieldtype: 'Date',
			label: __('From Date'),
			fieldname: 'from_date',
			reqd: 1,
		},
		render_input: true,
	});

	state.controls.to_date = frappe.ui.form.make_control({
		parent: $toWrap.get(0),
		df: {
			fieldtype: 'Date',
			label: __('To Date'),
			fieldname: 'to_date',
			reqd: 1,
		},
		render_input: true,
	});

	// Item Code control
	state.controls.item_code = frappe.ui.form.make_control({
		parent: $itemWrap.get(0),
		df: {
			fieldtype: 'Link',
			label: __('Item Code'),
			fieldname: 'item_code',
			options: 'Item',
			reqd: 0,
		},
		render_input: true,
	});

	// Refresh button
	const $refreshBtn = $('<button class="btn btn-primary">' + __('Refresh') + '</button>');
	$btnWrap.append($refreshBtn);
	state.controls.refreshBtn = $refreshBtn;

	// Apply black outline borders to filter fields
	setTimeout(() => {
		$(state.controls.from_date.$input).css({
			'border': '1px solid #000000',
			'border-radius': '4px',
			'padding': '8px 12px',
			'height': '36px',
			'line-height': '1.4'
		});
		$(state.controls.to_date.$input).css({
			'border': '1px solid #000000',
			'border-radius': '4px',
			'padding': '8px 12px',
			'height': '36px',
			'line-height': '1.4'
		});
		$(state.controls.item_code.$input).css({
			'border': '1px solid #000000',
			'border-radius': '4px',
			'padding': '8px 12px',
			'height': '36px',
			'line-height': '1.4'
		});
	}, 100);
}

function createTableContainer(state) {
	const $tableContainer = $('<div class="item-insight-table-container" style="margin-top:20px;"></div>');
	$(state.page.main).append($tableContainer);
	state.$tableContainer = $tableContainer;
}

function setDefaultFilters(state) {
	// Set default date range (last 30 days)
	const today = frappe.datetime.get_today();
	const fromDate = frappe.datetime.add_days(today, -30);
	
	state.controls.from_date.set_value(fromDate);
	state.controls.to_date.set_value(today);
}

function bindEventHandlers(state) {
	// Filter change events
	$(state.controls.from_date.$input).on('change', () => refreshDashboard(state));
	$(state.controls.to_date.$input).on('change', () => refreshDashboard(state));
	$(state.controls.item_code.$input).on('change', () => refreshDashboard(state));

	// Button events
	state.controls.refreshBtn.on('click', () => refreshDashboard(state));
}

function refreshDashboard(state) {
	console.log('Refreshing Item Insight Dashboard...');

	const filters = getFilters(state);

	if (!filters.from_date || !filters.to_date) {
		showError(state, __('Please select both From Date and To Date'));
		return;
	}

	// Show loading state
	state.page.set_indicator(__('Loading dashboard data...'), 'blue');

	// Fetch data
	frappe.call({
		method: 'prakash_steel.api.get_item_insight_data.get_item_insight_data',
		args: {
			from_date: filters.from_date,
			to_date: filters.to_date,
			item_code: filters.item_code || null
		},
		callback: function(r) {
			state.page.clear_indicator();

			if (r.message) {
				renderTable(state, r.message);
			} else {
				showError(state, __('No data available'));
			}
		},
		error: function(error) {
			state.page.clear_indicator();
			console.error('Dashboard refresh error:', error);
			showError(state, __('An error occurred while loading data'));
		}
	});
}

function getFilters(state) {
	return {
		from_date: state.controls.from_date.get_value(),
		to_date: state.controls.to_date.get_value(),
		item_code: state.controls.item_code.get_value()
	};
}

function renderTable(state, data) {
	state.$tableContainer.empty();

	if (!data || data.length === 0) {
		state.$tableContainer.append(`
			<div class="no-data-message" style="text-align:center;color:#7f8c8d;padding:24px;">
				<i class="fa fa-info-circle" style="font-size:2rem;margin-bottom:12px;"></i>
				<div>${__('No data available for selected criteria')}</div>
			</div>
		`);
		return;
	}

	// Create table with grouped columns
	const $table = $(`
		<div class="item-insight-table-wrapper" style="background:white;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
			<table class="item-insight-table" style="width:100%;border-collapse:separate;border-spacing:0;min-width:1600px;table-layout:fixed;">
				<thead>
					<tr>
						<!-- Item Details Group -->
						<th colspan="2" style="background:#e3f2fd;padding:12px;text-align:center;font-weight:600;color:#1976d2;border:1px solid #bbdefb;border-bottom:2px solid #1976d2;">
							${__('Item Details')}
						</th>
						<!-- Production Group -->
						<th colspan="2" style="background:#f3e5f5;padding:12px;text-align:center;font-weight:600;color:#7b1fa2;border:1px solid #ce93d8;border-bottom:2px solid #7b1fa2;">
							${__('Production')}
						</th>
						<!-- Sales Group -->
						<th colspan="4" style="background:#e8f5e9;padding:12px;text-align:center;font-weight:600;color:#388e3c;border:1px solid #a5d6a7;border-bottom:2px solid #388e3c;">
							${__('Sales')}
						</th>
						<!-- Purchase Group -->
						<th colspan="4" style="background:#fff3e0;padding:12px;text-align:center;font-weight:600;color:#f57c00;border:1px solid #ffcc80;border-bottom:2px solid #f57c00;">
							${__('Purchase')}
						</th>
						<!-- Warehouse Stock Group -->
						<th colspan="2" style="background:#fce4ec;padding:12px;text-align:center;font-weight:600;color:#c2185b;border:1px solid #f8bbd0;border-bottom:2px solid #c2185b;">
							${__('Warehouse Stock')}
						</th>
					</tr>
					<tr>
						<!-- Item Details Columns -->
						<th style="background:#f8f9fa;padding:10px;text-align:left;font-weight:600;color:#495057;border:1px solid #dee2e6;width:150px;min-width:150px;">${__('Item Code')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:left;font-weight:600;color:#495057;border:1px solid #dee2e6;width:200px;min-width:200px;">${__('Item Name')}</th>
						<!-- Production Columns -->
						<th style="background:#f8f9fa;padding:10px;text-align:left;font-weight:600;color:#495057;border:1px solid #dee2e6;width:140px;min-width:140px;">${__('Last Production Date')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:140px;min-width:140px;">${__('Last Production Qty')}</th>
						<!-- Sales Columns -->
						<th style="background:#f8f9fa;padding:10px;text-align:left;font-weight:600;color:#495057;border:1px solid #dee2e6;width:180px;min-width:180px;">${__('Last Sales Party')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:130px;min-width:130px;">${__('Last Sales Qty')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:130px;min-width:130px;">${__('Last Sales Rate')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:130px;min-width:130px;">${__('Pending SO Qty')}</th>
						<!-- Purchase Columns -->
						<th style="background:#f8f9fa;padding:10px;text-align:left;font-weight:600;color:#495057;border:1px solid #dee2e6;width:180px;min-width:180px;">${__('Last Purchase Party')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:140px;min-width:140px;">${__('Last Purchase Qty')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:140px;min-width:140px;">${__('Last Purchase Rate')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:140px;min-width:140px;">${__('Pending PO Qty')}</th>
						<!-- Warehouse Stock Columns -->
						<th style="background:#f8f9fa;padding:10px;text-align:left;font-weight:600;color:#495057;border:1px solid #dee2e6;width:200px;min-width:200px;">${__('Warehouse')}</th>
						<th style="background:#f8f9fa;padding:10px;text-align:right;font-weight:600;color:#495057;border:1px solid #dee2e6;width:120px;min-width:120px;">${__('Stock Qty')}</th>
					</tr>
				</thead>
				<tbody>
				</tbody>
			</table>
		</div>
	`);

	const $tbody = $table.find('tbody');

	// Render rows
	data.forEach((row, index) => {
		const rowId = `row-${index}`;
		
		// Main row
		const $mainRow = $(`
			<tr class="item-row" data-row-id="${rowId}" style="border-bottom:1px solid #e9ecef;">
				<!-- Item Details -->
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;width:150px;min-width:150px;">${frappe.utils.escape_html(row.item_code || '')}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;width:200px;min-width:200px;">${frappe.utils.escape_html(row.item_name || '')}</td>
				<!-- Production -->
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;width:140px;min-width:140px;">${row.last_production_date ? frappe.format(row.last_production_date, {fieldtype: 'Date'}) : '-'}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:140px;min-width:140px;">${frappe.format(row.last_production_quantity || 0, {fieldtype: 'Float', precision: 2})}</td>
				<!-- Sales -->
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;width:180px;min-width:180px;">${frappe.utils.escape_html(row.last_sales_party || '-')}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:130px;min-width:130px;">${frappe.format(row.last_sales_quantity || 0, {fieldtype: 'Float', precision: 2})}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:130px;min-width:130px;">${frappe.format(row.last_sales_rate || 0, {fieldtype: 'Currency', precision: 2})}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:130px;min-width:130px;">${frappe.format(row.pending_sales_order_qty || 0, {fieldtype: 'Float', precision: 2})}</td>
				<!-- Purchase -->
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;width:180px;min-width:180px;">${frappe.utils.escape_html(row.last_purchase_party || '-')}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:140px;min-width:140px;">${frappe.format(row.last_purchase_quantity || 0, {fieldtype: 'Float', precision: 2})}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:140px;min-width:140px;">${frappe.format(row.last_purchase_rate || 0, {fieldtype: 'Currency', precision: 2})}</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:140px;min-width:140px;">${frappe.format(row.pending_purchase_order_qty || 0, {fieldtype: 'Float', precision: 2})}</td>
				<!-- Warehouse Stock -->
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;width:200px;min-width:200px;">
					${row.warehouse_stock && row.warehouse_stock.length > 0 ? frappe.utils.escape_html(row.warehouse_stock[0].warehouse || '-') : '-'}
				</td>
				<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:120px;min-width:120px;">
					${row.warehouse_stock && row.warehouse_stock.length > 0 ? frappe.format(row.warehouse_stock[0].stock_qty || 0, {fieldtype: 'Float', precision: 2}) : '-'}
				</td>
			</tr>
		`);

		$tbody.append($mainRow);

		// Additional rows for multiple warehouses
		if (row.warehouse_stock && row.warehouse_stock.length > 1) {
			for (let i = 1; i < row.warehouse_stock.length; i++) {
				const wh = row.warehouse_stock[i];
				const $warehouseRow = $(`
					<tr class="warehouse-detail-row" data-parent-row="${rowId}" style="border-bottom:1px solid #e9ecef;">
						<!-- Empty cells for other columns -->
						<td style="padding:12px;border-right:1px solid #e9ecef;width:150px;min-width:150px;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;width:200px;min-width:200px;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<td style="padding:12px;border-right:1px solid #e9ecef;"></td>
						<!-- Warehouse Stock Columns -->
						<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;width:200px;min-width:200px;">${frappe.utils.escape_html(wh.warehouse || '-')}</td>
						<td style="padding:12px;border-right:1px solid #e9ecef;color:#495057;text-align:right;width:120px;min-width:120px;">${frappe.format(wh.stock_qty || 0, {fieldtype: 'Float', precision: 2})}</td>
					</tr>
				`);
				$tbody.append($warehouseRow);
			}
		}
	});

	state.$tableContainer.append($table);
}

function showError(state, message) {
	state.$tableContainer.empty();
	state.$tableContainer.append(`
		<div class="alert alert-danger" style="background:#f8d7da;border:1px solid #f5c6cb;color:#721c24;padding:16px;border-radius:8px;">
			<i class="fa fa-exclamation-triangle" style="margin-right:8px;"></i>
			${frappe.utils.escape_html(message)}
		</div>
	`);
}
