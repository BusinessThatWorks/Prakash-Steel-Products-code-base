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
				max-height: calc(100vh - 200px);
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
				border-collapse: separate;
				border-spacing: 0;
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
			/* Row separation - visible border lines only on last row of each item */
			.item-insight-table tbody tr.item-last-row {
				border-bottom: 1px solid #000000 !important;
			}
			.item-insight-table tbody tr.item-last-row td {
				border-bottom: 1px solid #000000 !important;
			}
			/* Alternating background colors - Cream shades */
			.item-insight-table tbody tr.item-bg-blue {
				background-color:rgb(255, 248, 220) !important;
			}
			.item-insight-table tbody tr.item-bg-green {
				background-color:rgb(250, 240, 230) !important;
			}
			.item-insight-table tbody tr.item-bg-blue:hover,
			.item-insight-table tbody tr.item-bg-green:hover {
				opacity: 0.9;
				transition: opacity 0.2s ease;
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

	// Bind event handlers
	bindEventHandlers(state);

	// Load ALL data on initial load (no spinner, no filters)
	loadInitialData(state);
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
	// Date controls - Not required, can be empty
	state.controls.from_date = frappe.ui.form.make_control({
		parent: $fromWrap.get(0),
		df: {
			fieldtype: 'Date',
			label: __('From Date'),
			fieldname: 'from_date',
			reqd: 0,
		},
		render_input: true,
	});

	state.controls.to_date = frappe.ui.form.make_control({
		parent: $toWrap.get(0),
		df: {
			fieldtype: 'Date',
			label: __('To Date'),
			fieldname: 'to_date',
			reqd: 0,
		},
		render_input: true,
	});

	// Item Code control - Using Data field with custom autocomplete
	state.controls.item_code = frappe.ui.form.make_control({
		parent: $itemWrap.get(0),
		df: {
			fieldtype: 'Data',
			label: __('Item Code'),
			fieldname: 'item_code',
			reqd: 0,
		},
		render_input: true,
	});

	// Setup custom autocomplete for Item Code field
	setTimeout(() => {
		setupItemCodeAutocomplete(state.controls.item_code);
	}, 300);

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

function setupItemCodeAutocomplete(control) {
	const $input = $(control.$input);
	let searchTimeout = null;
	
	// Add custom CSS for the dropdown
	if (!$('#item-code-autocomplete-style').length) {
		$('<style id="item-code-autocomplete-style">')
			.prop('type', 'text/css')
			.html(`
				.item-code-autocomplete {
					position: relative;
					display: inline-block;
					width: 100%;
				}
				.item-code-clear {
					position: absolute;
					right: 8px;
					top: 50%;
					transform: translateY(-50%);
					cursor: pointer;
					font-size: 20px;
					color: #888;
					font-weight: 600;
					line-height: 1;
					padding: 2px 6px;
					z-index: 10;
					user-select: none;
					transition: color 0.2s;
				}
				.item-code-clear:hover {
					color: #000;
				}
				.item-code-autocomplete input {
					padding-right: 30px !important;
				}
				.item-code-autocomplete ul {
					position: absolute;
					top: 100%;
					left: 0;
					right: 0;
					background: white;
					border: 1px solid #d1d8dd;
					border-radius: 4px;
					box-shadow: 0 2px 8px rgba(0,0,0,0.15);
					max-height: 300px;
					overflow-y: auto;
					z-index: 1000;
					margin-top: 2px;
					padding: 4px 0;
					list-style: none;
				}
				.item-code-autocomplete ul li {
					padding: 8px 12px;
					cursor: pointer;
					line-height: 1.6;
					border-bottom: 1px solid #f0f0f0;
				}
				.item-code-autocomplete ul li:last-child {
					border-bottom: none;
				}
				.item-code-autocomplete ul li:hover,
				.item-code-autocomplete ul li.selected {
					background-color: #f0f0f0;
				}
				.item-code-autocomplete ul li strong {
					display: block;
					margin-bottom: 2px;
					font-weight: 600;
					color: #000;
				}
				.item-code-autocomplete ul li span {
					display: block;
					color: #666;
					font-size: 0.9em;
				}
			`)
			.appendTo('head');
	}
	
	// Wrap input in autocomplete container
	if (!$input.parent().hasClass('item-code-autocomplete')) {
		$input.wrap('<div class="item-code-autocomplete"></div>');
	}
	
	const $container = $input.parent();
	
	// Add clear button
	const $clearBtn = $('<span class="item-code-clear" style="display:none;" title="Clear">&times;</span>').appendTo($container);
	
	const $dropdown = $('<ul style="display:none;"></ul>').appendTo($container);
	
	// Toggle clear button visibility based on input value
	function updateClearButton() {
		if ($input.val()) {
			$clearBtn.show();
		} else {
			$clearBtn.hide();
		}
	}
	
	// Clear button click handler
	$clearBtn.on('click', function(e) {
		e.stopPropagation();
		$input.val('');
		if (control.set_value) {
			control.set_value('');
		}
		$dropdown.hide();
		updateClearButton();
		$input.trigger('change');
	});
	
	// Update clear button on input change
	$input.on('input change', updateClearButton);
	
	// Initial update
	updateClearButton();
	
	// Search function
	function searchItems(query, immediate = false) {
		// Clear previous timeout
		clearTimeout(searchTimeout);
		
		// If no query, show all items (limited)
		if (!query || query.length < 1) {
			query = '';
		}
		
		const searchFn = () => {
			frappe.call({
				method: 'prakash_steel.api.get_item_insight_data.search_items',
				args: {
					query: query,
					limit: 20
				},
				callback: function(r) {
					if (r.message && r.message.length > 0) {
						renderDropdown(r.message, query);
					} else {
						$dropdown.hide().empty();
					}
				},
				error: function(err) {
					console.error('Error fetching items:', err);
					$dropdown.hide().empty();
				}
			});
		};
		
		// If immediate (on focus/click), don't debounce
		if (immediate) {
			searchFn();
		} else {
			// Debounce search for typing
			searchTimeout = setTimeout(searchFn, 300);
		}
	}
	
	// Render dropdown items
	function renderDropdown(items, query) {
		if (!items || items.length === 0) {
			$dropdown.hide().empty();
			return;
		}
		
		$dropdown.empty();
		
		items.forEach((item, index) => {
			const itemCode = item.name || '';
			const itemName = item.item_name || itemCode;
			const itemGroup = item.item_group || '';
			const description = itemGroup ? `${itemCode}, ${itemGroup}` : itemCode;
			
			const $li = $(`
				<li data-value="${frappe.utils.escape_html(itemCode)}" data-index="${index}">
					<strong>${frappe.utils.escape_html(itemName)}</strong>
					<span>${frappe.utils.escape_html(description)}</span>
				</li>
			`);
			
			$li.on('click', function() {
				const selectedValue = $(this).attr('data-value');
				$input.val(selectedValue);
				if (control.set_value) {
					control.set_value(selectedValue);
				}
				$dropdown.hide();
				updateClearButton();
				$input.trigger('change');
			});
			
			$li.on('mouseenter', function() {
				$dropdown.find('li').removeClass('selected');
				$(this).addClass('selected');
			});
			
			$dropdown.append($li);
		});
		
		$dropdown.show();
	}
	
	// Event handlers
	$input.on('input', function() {
		const query = $(this).val();
		searchItems(query, false);
	});
	
	$input.on('focus click', function() {
		const query = $(this).val();
		// Show dropdown immediately on focus/click
		searchItems(query, true);
	});
	
	$input.on('blur', function() {
		// Delay hiding to allow click events
		setTimeout(() => {
			$dropdown.hide();
		}, 200);
	});
	
	// Keyboard navigation
	$input.on('keydown', function(e) {
		const $items = $dropdown.find('li');
		const $selected = $dropdown.find('li.selected');
		
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			if ($selected.length) {
				const next = $selected.next();
				if (next.length) {
					$selected.removeClass('selected');
					next.addClass('selected');
					next[0].scrollIntoView({ block: 'nearest' });
				}
			} else if ($items.length) {
				$items.first().addClass('selected');
			}
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			if ($selected.length) {
				const prev = $selected.prev();
				if (prev.length) {
					$selected.removeClass('selected');
					prev.addClass('selected');
					prev[0].scrollIntoView({ block: 'nearest' });
				}
			}
		} else if (e.key === 'Enter') {
			e.preventDefault();
			if ($selected.length) {
				const selectedValue = $selected.attr('data-value');
				$input.val(selectedValue);
				if (control.set_value) {
					control.set_value(selectedValue);
				}
				$dropdown.hide();
				updateClearButton();
				$input.trigger('change');
			}
		} else if (e.key === 'Escape') {
			$dropdown.hide();
		}
	});
	
	// Hide dropdown when clicking outside
	$(document).on('click', function(e) {
		if (!$container.is(e.target) && $container.has(e.target).length === 0) {
			$dropdown.hide();
		}
	});
}

function createTableContainer(state) {
	const $tableContainer = $('<div class="item-insight-table-container" style="margin-top:20px;"></div>');
	$(state.page.main).append($tableContainer);
	state.$tableContainer = $tableContainer;
}

function loadInitialData(state) {
	// Load ALL data on initial load - NO loading UI, NO filters
	// Data will appear directly when API returns
	frappe.call({
		method: 'prakash_steel.api.get_item_insight_data.get_item_insight_data',
		args: {
			from_date: null,
			to_date: null,
			item_code: null
		},
		async: true,
		callback: function(r) {
			if (r && r.message && r.message.length > 0) {
				renderTable(state, r.message);
			} else {
				showNoData(state);
			}
		},
		error: function(error) {
			console.error('Initial load error:', error);
			showError(state, __('Failed to load data'));
		}
	});
}

function bindEventHandlers(state) {
	// Debounce to prevent multiple rapid calls
	let refreshTimeout;
	function debouncedRefresh() {
		clearTimeout(refreshTimeout);
		refreshTimeout = setTimeout(() => {
			refreshDashboard(state);
		}, 300);
	}
	
	// Filter change events - Date fields
	// Trigger on any change (including clear)
	$(state.controls.from_date.$input).on('change', debouncedRefresh);
	$(state.controls.to_date.$input).on('change', debouncedRefresh);
	
	// Item Code field - trigger on change
	$(state.controls.item_code.$input).on('change', debouncedRefresh);

	// Button events - direct refresh
	state.controls.refreshBtn.on('click', () => refreshDashboard(state));
}

function refreshDashboard(state, showSpinner = true) {
	// Called when filters change - fetches filtered data
	const filters = getFilters(state);

	// Check if any filter is set
	const hasDateFilter = filters.from_date && filters.to_date;
	const hasItemFilter = filters.item_code;
	
	// If no filters are set, load all data (revert to initial state)
	if (!hasDateFilter && !hasItemFilter) {
		// Don't show spinner when clearing filters - just reload all data
		frappe.call({
			method: 'prakash_steel.api.get_item_insight_data.get_item_insight_data',
			args: {
				from_date: null,
				to_date: null,
				item_code: null
			},
			callback: function(r) {
				if (r && r.message && r.message.length > 0) {
					renderTable(state, r.message);
				} else {
					showNoData(state);
				}
			},
			error: function(error) {
				console.error('Dashboard refresh error:', error);
				showError(state, __('An error occurred while loading data'));
			}
		});
		return;
	}

	// Show loading spinner only when filters are being applied
	if (showSpinner) {
		showLoading(state);
	}

	// Fetch filtered data
	frappe.call({
		method: 'prakash_steel.api.get_item_insight_data.get_item_insight_data',
		args: {
			from_date: filters.from_date || null,
			to_date: filters.to_date || null,
			item_code: filters.item_code || null
		},
		callback: function(r) {
			if (r && r.message && r.message.length > 0) {
				renderTable(state, r.message);
			} else {
				showNoData(state);
			}
		},
		error: function(error) {
			console.error('Dashboard refresh error:', error);
			showError(state, __('An error occurred while loading data'));
		}
	});
}

function showNoData(state) {
	state.$tableContainer.empty();
	state.$tableContainer.append(`
		<div class="no-data-message" style="text-align:center;color:#7f8c8d;padding:40px;">
			<i class="fa fa-inbox" style="font-size:3rem;margin-bottom:16px;color:#bdc3c7;"></i>
			<div style="font-size:1.1rem;">${__('No data found for the selected criteria')}</div>
		</div>
	`);
}

function getFilters(state) {
	return {
		from_date: state.controls.from_date.get_value(),
		to_date: state.controls.to_date.get_value(),
		item_code: state.controls.item_code.get_value()
	};
}

function renderTable(state, data) {
	try {
		console.log('renderTable called with data:', data);
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
		<div class="item-insight-table-wrapper" style="background:white;border-radius:8px;border:1px solid #000000;">
			<table class="item-insight-table" style="width:100%;border-collapse:separate;border-spacing:0;min-width:1400px;table-layout:fixed;">
				<thead>
				<tr>
					<!-- Item Details Group -->
					<th colspan="1" style="background:#d2b48c;padding:12px;text-align:center;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;">
						${__('Item Details')}
					</th>
						<!-- Production Group -->
						<th colspan="2" style="background:#d2b48c;padding:12px;text-align:center;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;">
							${__('Production')}
						</th>
						<!-- Sales Group -->
						<th colspan="5" style="background:#d2b48c;padding:12px;text-align:center;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;">
							${__('Sales')}
						</th>
						<!-- Purchase Group -->
						<th colspan="5" style="background:#d2b48c;padding:12px;text-align:center;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;">
							${__('Purchase')}
						</th>
						<!-- Warehouse Stock Group -->
						<th colspan="2" style="background:#d2b48c;padding:12px;text-align:center;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;">
							${__('Warehouse Stock')}
						</th>
					</tr>
					<tr>
						<!-- Item Details Columns -->
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;width:150px;min-width:150px;">${__('Item Code')}</th>
						<!-- Production Columns -->
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:140px;min-width:140px;">${__('Last Production Date')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;width:140px;min-width:140px;">${__('Last Production Qty')}</th>
						<!-- Sales Columns -->
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:180px;min-width:180px;">${__('Last Sales Party')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:140px;min-width:140px;">${__('Last Sales Date')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:130px;min-width:130px;">${__('Last Sales Qty')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:130px;min-width:130px;">${__('Last Sales Rate')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;width:130px;min-width:130px;">${__('Pending SO Qty')}</th>
						<!-- Purchase Columns -->
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:180px;min-width:180px;">${__('Last Purchase Party')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:140px;min-width:140px;">${__('Last Purchase Date')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:140px;min-width:140px;">${__('Last Purchase Qty')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:140px;min-width:140px;">${__('Last Purchase Rate')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;width:140px;min-width:140px;">${__('Pending PO Qty')}</th>
						<!-- Warehouse Stock Columns -->
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:1px solid #000000;border-bottom:1px solid #000000;width:200px;min-width:200px;">${__('Warehouse')}</th>
						<th style="background:#faf0e6;padding:10px;text-align:left;font-weight:600;color:#000000;border-right:2px solid #000000;border-bottom:1px solid #000000;width:120px;min-width:120px;">${__('Stock Qty')}</th>
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
		
		// Determine background color based on item index (alternating blue and green)
		const isEvenItem = index % 2 === 0;
		const itemBgClass = isEvenItem ? 'item-bg-blue' : 'item-bg-green';
		
		// Main row
		const $mainRow = $(`
			<tr class="item-row ${itemBgClass}" data-row-id="${rowId}" data-item-index="${index}">
				<!-- Item Details -->
				<td style="padding:12px;border-right:2px solid #000000;color:#495057;width:150px;min-width:150px;">${frappe.utils.escape_html(row.item_code || '')}</td>
				<!-- Production -->
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;width:140px;min-width:140px;">${row.last_production_date ? frappe.format(row.last_production_date, {fieldtype: 'Date'}) : '-'}</td>
				<td style="padding:12px;border-right:2px solid #000000;color:#495057;text-align:left;width:140px;min-width:140px;">${frappe.format(row.last_production_quantity || 0, {fieldtype: 'Float', precision: 2})}</td>
				<!-- Sales -->
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;width:180px;min-width:180px;">${frappe.utils.escape_html(row.last_sales_party || '-')}</td>
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;text-align:left;width:140px;min-width:140px;">${row.last_sales_date ? frappe.format(row.last_sales_date, {fieldtype: 'Date'}) : '-'}</td>
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;text-align:left;width:130px;min-width:130px;">${frappe.format(row.last_sales_quantity || 0, {fieldtype: 'Float', precision: 2})}</td>
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;text-align:left;width:130px;min-width:130px;">${frappe.format(row.last_sales_rate || 0, {fieldtype: 'Currency', precision: 2})}</td>
				<td style="padding:12px;border-right:2px solid #000000;color:#495057;text-align:left;width:130px;min-width:130px;">${frappe.format(row.pending_sales_order_qty || 0, {fieldtype: 'Float', precision: 2})}</td>
				<!-- Purchase -->
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;width:180px;min-width:180px;">${frappe.utils.escape_html(row.last_purchase_party || '-')}</td>
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;text-align:left;width:140px;min-width:140px;">${row.last_purchase_date ? frappe.format(row.last_purchase_date, {fieldtype: 'Date'}) : '-'}</td>
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;text-align:left;width:140px;min-width:140px;">${frappe.format(row.last_purchase_quantity || 0, {fieldtype: 'Float', precision: 2})}</td>
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;text-align:left;width:140px;min-width:140px;">${frappe.format(row.last_purchase_rate || 0, {fieldtype: 'Currency', precision: 2})}</td>
				<td style="padding:12px;border-right:2px solid #000000;color:#495057;text-align:left;width:140px;min-width:140px;">${frappe.format(row.pending_purchase_order_qty || 0, {fieldtype: 'Float', precision: 2})}</td>
				<!-- Warehouse Stock -->
				<td style="padding:12px;border-right:1px solid #000000;color:#495057;width:200px;min-width:200px;">
					${row.warehouse_stock && row.warehouse_stock.length > 0 ? frappe.utils.escape_html(row.warehouse_stock[0].warehouse || '-') : '-'}
				</td>
				<td style="padding:12px;border-right:2px solid #000000;color:#495057;text-align:left;width:120px;min-width:120px;">
					${row.warehouse_stock && row.warehouse_stock.length > 0 ? frappe.format(row.warehouse_stock[0].stock_qty || 0, {fieldtype: 'Float', precision: 2}) : '-'}
				</td>
			</tr>
		`);

		// Check if this item has multiple warehouses
		const hasMultipleWarehouses = row.warehouse_stock && row.warehouse_stock.length > 1;
		
		// If no multiple warehouses, mark main row as last row of this item
		if (!hasMultipleWarehouses) {
			$mainRow.addClass('item-last-row');
		}
		
		$tbody.append($mainRow);

		// Additional rows for multiple warehouses
		if (hasMultipleWarehouses) {
			for (let i = 1; i < row.warehouse_stock.length; i++) {
				const wh = row.warehouse_stock[i];
				const isLastWarehouse = (i === row.warehouse_stock.length - 1);
				const rowClass = isLastWarehouse ? `warehouse-detail-row item-last-row ${itemBgClass}` : `warehouse-detail-row ${itemBgClass}`;
				
				const $warehouseRow = $(`
					<tr class="${rowClass}" data-parent-row="${rowId}" data-item-index="${index}">
						<!-- Empty cells for other columns -->
						<td style="padding:12px;border-right:2px solid #000000;width:150px;min-width:150px;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:2px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:2px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:1px solid #000000;"></td>
						<td style="padding:12px;border-right:2px solid #000000;"></td>
						<!-- Warehouse Stock Columns -->
						<td style="padding:12px;border-right:1px solid #000000;color:#495057;width:200px;min-width:200px;">${frappe.utils.escape_html(wh.warehouse || '-')}</td>
						<td style="padding:12px;border-right:2px solid #000000;color:#495057;text-align:left;width:120px;min-width:120px;">${frappe.format(wh.stock_qty || 0, {fieldtype: 'Float', precision: 2})}</td>
					</tr>
				`);
				$tbody.append($warehouseRow);
			}
		}
	});

	state.$tableContainer.append($table);
		console.log('Table rendered successfully');
	} catch (error) {
		console.error('Error rendering table:', error);
		showError(state, __('Error rendering table: ') + error.message);
	}
}

function showLoading(state) {
	state.$tableContainer.empty();
	state.$tableContainer.append(`
		<div class="loading-message" style="text-align:center;color:#7f8c8d;padding:24px;">
			<i class="fa fa-spinner fa-spin" style="font-size:2rem;margin-bottom:12px;"></i>
			<div>${__('Loading data...')}</div>
		</div>
	`);
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
