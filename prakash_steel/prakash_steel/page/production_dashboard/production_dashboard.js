// Copyright (c) 2025, Prakash Steel and contributors
// For license information, please see license.txt

// ================================================================
// Production Dashboard – Rolled & Bright Production Tabs
// ================================================================

if (!frappe.pages['production-dashboard']) {
    frappe.pages['production-dashboard'] = {};
}

frappe.pages['production-dashboard'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Production Dashboard'),
        single_column: true,
    });

    const state = {
        page,
        wrapper,
        $cards: null,
        $tabs: null,
        controls: {},
        currentTab: 'rolled_production',
        _refreshTimer: null,
        _refreshGen: 0,
    };

    initializeDashboard(state);
};

frappe.pages['production-dashboard'].on_page_show = function () {};

// ────────────────────────────────────────────────────────────────
// Initialization
// ────────────────────────────────────────────────────────────────
function initializeDashboard(state) {
    state.page.main.empty();

    render_filters(state);
    createTabbedInterface(state);
    createContentContainers(state);
    bindEventHandlers(state);

    // Apply active tab styling on first load
    updateTabStyles(state);

    // Initial data load - fetch data till date (filters remain empty in UI)
    refreshDashboard(state);
}

// ────────────────────────────────────────────────────────────────
// Filters
// ────────────────────────────────────────────────────────────────
function render_filters(state) {
    const $filterBar = $(`
        <div class="production-filters"
             style="display:flex;gap:12px;align-items:end;flex-wrap:wrap;
                    margin-bottom:16px;background:#f8f9fa;padding:16px;
                    border-radius:8px;">
        </div>`);

    const $filterControls = $('<div style="display:flex;gap:12px;align-items:end;flex-wrap:wrap;width:100%;"></div>');

    const $fromDateWrap = $('<div style="flex:1;min-width:200px;"></div>');
    const $toDateWrap   = $('<div style="flex:1;min-width:200px;"></div>');
    const $itemWrap     = $('<div style="flex:1;min-width:250px;"></div>');
    const $ppWrap       = $('<div style="flex:1;min-width:250px;"></div>');
    const $machineWrap  = $('<div style="flex:1;min-width:250px;"></div>');

    $filterControls
        .append($fromDateWrap)
        .append($toDateWrap)
        .append($itemWrap)
        .append($ppWrap)
        .append($machineWrap);

    $filterBar.append($filterControls);
    $(state.page.main).append($filterBar);

    // ── From Date ──
    state.controls.from_date = frappe.ui.form.make_control({
        parent: $fromDateWrap.get(0),
        df: { fieldtype: 'Date', label: __('From Date'), fieldname: 'from_date', reqd: 0 },
        render_input: true,
    });

    // ── To Date ──
    state.controls.to_date = frappe.ui.form.make_control({
        parent: $toDateWrap.get(0),
        df: { fieldtype: 'Date', label: __('To Date'), fieldname: 'to_date', reqd: 0 },
        render_input: true,
    });

    // ── Item Code ──
    state.controls.item_code = frappe.ui.form.make_control({
        parent: $itemWrap.get(0),
        df: { fieldtype: 'Link', label: __('Item Code'), fieldname: 'item_code', options: 'Item', reqd: 0 },
        render_input: true,
    });

    // ── Production Plan (tab-aware query) ──
    state.controls.production_plan = frappe.ui.form.make_control({
        parent: $ppWrap.get(0),
        df: {
            fieldtype: 'Link',
            label: __('Production Plan'),
            fieldname: 'production_plan',
            options: 'Production Plan',
            reqd: 0,
            get_query: function () {
                return getProductionPlanQuery(state);
            },
        },
        render_input: true,
    });

    // ── Machine Name ──
    state.controls.machine_name = frappe.ui.form.make_control({
        parent: $machineWrap.get(0),
        df: {
            fieldtype: 'Link',
            label: __('Machine Name'),
            fieldname: 'machine_name',
            options: 'Machine Master',
            reqd: 0,
        },
        render_input: true,
    });

    // ── Style inputs ──
    setTimeout(() => {
        [state.controls.from_date, state.controls.to_date,
         state.controls.item_code, state.controls.production_plan,
         state.controls.machine_name].forEach(c => {
            if (c && c.$input) {
                $(c.$input).css({
                    border: '1px solid #000', 'border-radius': '4px',
                    padding: '8px 12px', height: '36px', 'line-height': '1.4',
                });
            }
        });
    }, 100);
}


function getProductionPlanQuery(state) {
    const filters = { docstatus: 1 };
    if (state.currentTab === 'rolled_production') {
        filters['name'] = ['like', '%Rolled%'];
    } else if (state.currentTab === 'bright_production') {
        filters['name'] = ['like', '%Bright%'];
    }
    return { filters };
}

function getFilters(state) {
    return {
        from_date: state.controls.from_date ? state.controls.from_date.get_value() : null,
        to_date: state.controls.to_date ? state.controls.to_date.get_value() : null,
        item_code: state.controls.item_code ? state.controls.item_code.get_value() : null,
        production_plan: state.controls.production_plan ? state.controls.production_plan.get_value() : null,
        machine_name: state.controls.machine_name ? state.controls.machine_name.get_value() : null,
    };
}

// ────────────────────────────────────────────────────────────────
// Tabs
// ────────────────────────────────────────────────────────────────
function createTabbedInterface(state) {
    const $tabContainer = $('<div class="production-tabs" style="margin-bottom:20px;"></div>');
    const $tabList = $('<ul class="nav nav-tabs" role="tablist" style="border-bottom:2px solid #dee2e6;"></ul>');
    const $tabContent = $('<div class="tab-content" style="margin-top:20px;"></div>');

    const tabs = [
        { id: 'rolled_production', label: __('Rolled Production'), icon: 'fa fa-industry' },
        { id: 'bright_production', label: __('Bright Production'), icon: 'fa fa-cog' },
        { id: 'bend_weight_details', label: __('Bend Weight Details'), icon: 'fa fa-balance-scale' },
    ];

    tabs.forEach((tab, idx) => {
        const $tabItem = $(`
            <li class="nav-item" role="presentation">
                <button class="nav-link ${idx === 0 ? 'active' : ''}"
                        id="${tab.id}-tab" type="button" role="tab"
                        style="border:none;background:none;padding:12px 20px;
                               color:#6c757d;font-weight:500;cursor:pointer;">
                    <i class="${tab.icon}" style="margin-right:8px;"></i>${tab.label}
                </button>
            </li>`);

        const $tabPane = $(`
            <div class="tab-pane fade ${idx === 0 ? 'show active' : ''}"
                 id="${tab.id}-content" role="tabpanel" style="min-height:400px;">
            </div>`);

        $tabList.append($tabItem);
        $tabContent.append($tabPane);

        if (!state.$tabs) state.$tabs = {};
        state.$tabs[tab.id] = { $item: $tabItem, $content: $tabPane };
    });

    $tabContainer.append($tabList).append($tabContent);
    $(state.page.main).append($tabContainer);
}

function createContentContainers(state) {
    Object.keys(state.$tabs).forEach(tabId => {
        // Cards
        const $cards = $('<div class="number-cards-container" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-bottom:24px;"></div>');
        state.$tabs[tabId].$content.append($cards);
        if (!state.$cards) state.$cards = {};
        state.$cards[tabId] = $cards;

        // Table
        let title;
        if (tabId === 'rolled_production') {
            title = __('Rolled Production Details');
        } else if (tabId === 'bright_production') {
            title = __('Bright Production Details');
        } else if (tabId === 'bend_weight_details') {
            title = __('Bend Weight Details');
        } else {
            title = '';
        }

        const $tableSection = $(`
            <div class="detailed-data-section">
                <h3 style="margin-bottom:16px;color:#495057;font-weight:600;">${title}</h3>
                <div class="data-tables-container" id="${tabId}-tables"
                     style="overflow-x:auto;"></div>
            </div>`);
        state.$tabs[tabId].$content.append($tableSection);
    });

    // Initialize with empty states
    render_cards(state, {});
    render_table(state, []);
}

// ────────────────────────────────────────────────────────────────
// Event Handlers
// ────────────────────────────────────────────────────────────────
function bindEventHandlers(state) {
    // ── Auto-refresh on filter change (immediate, no debounce) ──
    const handler = () => refreshDashboard(state);

    [state.controls.from_date, state.controls.to_date,
     state.controls.item_code, state.controls.production_plan,
     state.controls.machine_name].forEach(c => {
        if (!c) return;
        c.df.change = handler;
        c.df.onchange = handler;
        if (c.$input) {
            $(c.$input).on('change', handler);
        }
        if (c.df.fieldtype === 'Link' && c.$input) {
            $(c.$input).on('awesomplete-selectcomplete', handler);
            if (c.$wrapper) $(c.$wrapper).on('click', '.btn-clear', handler);
        }
    });

    // ── Tab switching ──
    Object.keys(state.$tabs).forEach(tabId => {
        state.$tabs[tabId].$item.find('button').on('click', () => {
            state.currentTab = tabId;
            updateTabStyles(state);

            $('.tab-pane').removeClass('show active');
            $(`#${tabId}-content`).addClass('show active');
            $('.nav-link').removeClass('active');
            $(`#${tabId}-tab`).addClass('active');

            // Clear production plan value when switching tabs (different filter context)
            if (state.controls.production_plan) {
                state.controls.production_plan.set_value('');
            }

            // Always refresh on tab switch (will fetch till date if no filters set)
            refreshDashboard(state);
        });
    });
}

function updateTabStyles(state) {
    Object.keys(state.$tabs).forEach(tabId => {
        const $btn = state.$tabs[tabId].$item.find('button');
        if (tabId === state.currentTab) {
            $btn.addClass('active').css({ color: '#007bff', 'border-bottom': '2px solid #007bff' });
        } else {
            $btn.removeClass('active').css({ color: '#6c757d', 'border-bottom': 'none' });
        }
    });
}

// ────────────────────────────────────────────────────────────────
// Data Fetch & Render Orchestrator
// ────────────────────────────────────────────────────────────────
function refreshDashboard(state) {
    const filters = getFilters(state);
    const tabId = state.currentTab;

    // Stale-response guard
    state._refreshGen = (state._refreshGen || 0) + 1;
    const thisGen = state._refreshGen;

    state.page.set_indicator(__('Loading…'), 'blue');

    let apiMethod;
    if (tabId === 'rolled_production') {
        apiMethod = 'prakash_steel.api.production_dashboard.get_rolled_production_data';
    } else if (tabId === 'bright_production') {
        apiMethod = 'prakash_steel.api.production_dashboard.get_bright_production_data';
    } else if (tabId === 'bend_weight_details') {
        apiMethod = 'prakash_steel.api.production_dashboard.get_bend_weight_details';
    }

    // If no date filters are set, fetch data till today (but keep UI filters empty)
    const from_date = filters.from_date || '';
    const to_date = filters.to_date || (filters.from_date ? '' : frappe.datetime.get_today());

    frappe.call({
        method: apiMethod,
        args: {
            from_date: from_date,
            to_date: to_date,
            item_code: filters.item_code || '',
            production_plan: filters.production_plan || '',
            machine_name: filters.machine_name || '',
        },
        callback: function (r) {
            if (state._refreshGen !== thisGen) return; // stale
            state.page.clear_indicator();

            const data = r.message || { rows: [], totals: {} };
            render_cards(state, data.totals);
            render_table(state, data.rows);
        },
        error: function () {
            if (state._refreshGen !== thisGen) return;
            state.page.clear_indicator();
            render_cards(state, { total_production: 0, rm_consumption: 0 });
            render_table(state, []);
            frappe.show_alert({ message: __('Error loading production data'), indicator: 'red' });
        },
    });
}

// ────────────────────────────────────────────────────────────────
// KPI Cards
// ────────────────────────────────────────────────────────────────
function render_cards(state, totals) {
    const tabId = state.currentTab;
    const $container = state.$cards[tabId];
    $container.empty();

    totals = totals || {};

    // For Bend Weight Details, skip KPI cards for now
    if (tabId === 'bend_weight_details') {
        return;
    }

    const gradientClasses = tabId === 'rolled_production'
        ? [] // we will assign explicit colors below
        : ['card-yellow', 'card-green', 'card-orange'];

    const cards = [
        {
            value: totals.total_production,
            label: __('Total Production (kg)'),
            gradientClass: tabId === 'rolled_production' ? 'card-blue' : gradientClasses[0],
            description: __('Sum of Actual Qty across all rows'),
            isQty: true,
        },
        {
            value: totals.rm_consumption,
            label: __('RM Consumption'),
            gradientClass: tabId === 'rolled_production' ? 'card-teal' : gradientClasses[1],
            description: __('Sum of RM Consumption across all rows'),
            isQty: true,
        },
    ];

    // Tab-specific KPI cards
    if (tabId === 'rolled_production') {
        const totalProd = parseFloat(totals.total_production) || 0;
        const totalHr = parseFloat(totals.total_hr_consumed) || 0;
        const totalMeltingWeight = parseFloat(totals.total_melting_weight) || 0;
        const totalMissBilletWeight = parseFloat(totals.total_miss_billet_weight) || 0;
        const totalMissRollWeight = parseFloat(totals.total_miss_roll_weight) || 0;
        const totalMissIngotWeight = parseFloat(totals.total_miss_ingot_weight) || 0;

        // Total Hr = Sum of Total Hr Consumed
        cards.push({
            value: totalHr,
            label: __('Total Hr'),
            gradientClass: 'card-yellow',
            description: __('Sum of Total Hr Consumed'),
        });

        // Average Production = Total Production / Sum(Total Hr Consumed)
        let avgProduction = 0;
        if (totalHr > 0) {
            avgProduction = totalProd / totalHr;
        }

        cards.push({
            value: avgProduction,
            label: __('Average Production'),
            gradientClass: 'card-red',
            description: __('Total Production / Total Hr Consumed'),
        });

        // Total Melting Weight
        cards.push({
            value: totalMeltingWeight,
            label: __('Total Melting Weight'),
            gradientClass: 'card-green',
            description: __('Sum of Melting Weight across all rows'),
            isQty: true,
        });

        // Total Miss Billet Weight
        cards.push({
            value: totalMissBilletWeight,
            label: __('Total Miss Billet Weight(RM)'),
            gradientClass: 'card-pink',
            description: __('Sum of Miss Billet Weight across all rows'),
            isQty: true,
        });

        // Total Miss Roll Weight
        cards.push({
            value: totalMissRollWeight,
            label: __('Total Miss Roll Weight(FG)'),
            gradientClass: 'card-orange',
            description: __('Sum of Total Miss Roll Weight across all rows'),
            isQty: true,
        });

        // Total Miss Ingot / Billet Weight
        cards.push({
            value: totalMissIngotWeight,
            label: __('Total Miss Ingot / Billet Weight(FG)'),
            gradientClass: 'card-purple',
            description: __('Sum of Total Miss Ingot / Billet Weight across all rows'),
            isQty: true,
        });

        // Burning Loss % — Average from Finish Weight records (backend calculated)
        cards.push({
            value: totals.burning_loss_per,
            label: __('Burning Loss %'),
            gradientClass: 'card-red',
            description: __('Average Burning Loss % (from Finish Weight)'),
            isPercentage: true,
        });

    } else if (tabId === 'bright_production') {
        // Melting Weight — Sum from Bright Bar Production (backend calculated)
        cards.push({
            value: totals.total_fg_weight,
            label: __('Melting Weight'),
            gradientClass: 'card-teal',
            description: __('Total Melting Weight (from Bright Bar Production)'),
            isQty: true,
        });

        // Wastage % — Average from Bright Bar Production records (backend calculated)
        cards.push({
            value: totals.wastage_per,
            label: __('Wastage %'),
            gradientClass: gradientClasses[2],
            description: __('Average Wastage % (from Bright Bar Production)'),
            isPercentage: true,
        });
    }

    cards.forEach(card => {
        $container.append(buildCardHtml(card));
    });
}

// Helper function to format Qty fields: truncate (don't round) and show as INTEGER only
function format_qty_as_integer(value) {
    if (value === undefined || value === null || value === '') {
        return '--';
    }
    const num = parseFloat(value);
    if (isNaN(num)) {
        return '--';
    }
    const truncated = Math.trunc(num);
    return format_number(truncated, null, 0);
}

// Helper function to format other numeric fields: keep decimal values as is (no rounding)
function format_number_with_decimals(value) {
    if (value === undefined || value === null || value === '') {
        return '--';
    }
    const num = parseFloat(value);
    if (isNaN(num)) {
        return '--';
    }
    return format_number(num);
}

// Helper function to format percentage values: show exactly 2 decimal places
function format_percentage(value) {
    if (value === undefined || value === null || value === '') {
        return '--';
    }
    const num = parseFloat(value);
    if (isNaN(num)) {
        return '--';
    }
    return num.toFixed(2);
}

function buildCardHtml(card) {
    const raw = card.value;
    let display;
    if (card.isQty) {
        display = format_qty_as_integer(raw);
    } else if (card.isPercentage) {
        display = format_percentage(raw);
    } else {
        display = format_number_with_decimals(raw);
    }

    const gradientClass = card.gradientClass || 'card-blue';
    const gradient = getGradientStyle(gradientClass);

    const desc = card.description
        ? `<div style="font-size:0.85rem;color:#000;margin-top:8px;opacity:0.7;">${frappe.utils.escape_html(card.description)}</div>`
        : '';

    return $(`
        <div class="number-card ${gradientClass}"
             style="background:${gradient} !important;background-image:${gradient} !important;
                    border-radius:10px;padding:14px 18px;
                    box-shadow:none;min-height:110px;
                    position:relative;overflow:hidden;
                    transition:transform .2s,box-shadow .2s;
                    color:#000;border:none;">
            <div style="text-align:center;">
                <div style="font-size:1.9rem;font-weight:700;color:#000;
                            margin-bottom:6px;line-height:1.1;">${display}</div>
                <div style="font-size:0.95rem;color:#000;font-weight:500;opacity:0.95;">
                    ${frappe.utils.escape_html(card.label || '')}</div>
                ${desc}
            </div>
        </div>`);
}

function getGradientStyle(gradientClass) {
    const gradients = {
        'card-orange': 'linear-gradient(135deg, #fdd085, #fde0a8)',
        'card-blue':   'linear-gradient(135deg, #a8c8f0, #c4d9f5)',
        'card-green':  'linear-gradient(135deg, #85e0a8, #a8ecc4)',
        'card-purple': 'linear-gradient(135deg, #c9a5d9, #d9b8e6)',
        'card-teal':   'linear-gradient(135deg, #7dd3c0, #a3e4d4)',
        'card-red':    'linear-gradient(135deg, #f5a5a0, #f8b8b3)',
        'card-pink':   'linear-gradient(135deg, #f8c8d8, #fce0e8)',
        'card-yellow': 'linear-gradient(135deg, #d4a574, #e8d5b7)',
    };
    return gradients[gradientClass] || gradients['card-blue'];
}

// ────────────────────────────────────────────────────────────────
// Table Rendering
// ────────────────────────────────────────────────────────────────
function render_table(state, rows) {
    const tabId = state.currentTab;
    const $container = $(`#${tabId}-tables`);
    $container.empty();

    const columns = getTableColumns(tabId);

    // ── Export toolbar (Excel / PDF) ──
    const $exportBar = buildExportToolbar(state, tabId, columns, rows || []);
    $container.append($exportBar);

    // ── Header ──
    const thBase = 'background:#495057;padding:12px;font-weight:600;color:#ffffff;'
        + 'border-bottom:2px solid #343a40;white-space:nowrap;text-align:center !important;'
        + 'position:sticky;top:0;z-index:2;';

    const thCol0 = thBase.replace('z-index:2', 'z-index:3') + 'left:0;min-width:180px;';
    const thCol1 = thBase.replace('z-index:2', 'z-index:3')
        + 'left:180px;min-width:140px;border-right:2px solid #dee2e6;';

    const headerHtml = columns.map((c, idx) => {
        const borderAfterQty =
            (tabId === 'rolled_production' && (idx === 11 || idx === 21)) ||
            (tabId === 'bright_production' && idx === 5);
        const borderRight = borderAfterQty ? ' border-right:2px solid #dee2e6;' : '';
        let style;
        if (idx === 0) style = thCol0;
        else if (idx === 1) style = thCol1;
        else style = thBase;
        return `<th style="${style}${borderRight}">${c.label}</th>`;
    }).join('');

    // ── Body ──
    let bodyHtml = '';
    if (!rows || rows.length === 0) {
        bodyHtml = `<tr><td colspan="${columns.length}"
            style="padding:24px;text-align:center;color:#7f8c8d;font-style:italic;">
            ${__('No data available for the selected filters.')}</td></tr>`;
    } else {
        bodyHtml = rows.map(row => buildTableRow(tabId, row)).join('');
    }

    const $table = $(`
        <div style="width:100%;margin-bottom:30px;overflow:auto;max-height:70vh;
                    border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <table style="width:100%;border-collapse:separate;border-spacing:0;
                          background:#fff;min-width:1000px;">
                <thead><tr>${headerHtml}</tr></thead>
                <tbody>${bodyHtml}</tbody>
            </table>
        </div>`);

    $container.append($table);
}

function buildTableRow(tabId, row) {
    const tdStyle = 'padding:12px;border-bottom:1px solid #e9ecef;color:#495057;text-align:center !important;';
    const tdCol0 = tdStyle + 'position:sticky;left:0;z-index:1;background:#fff;min-width:180px;';
    const tdCol1 = tdStyle + 'position:sticky;left:180px;z-index:1;background:#fff;min-width:140px;border-right:2px solid #dee2e6;';

    // Production Plan (link)
    const ppLink = row.production_plan
        ? `<a href="/app/production-plan/${encodeURIComponent(row.production_plan)}"
              style="color:#007bff;text-decoration:none;">${frappe.utils.escape_html(row.production_plan)}</a>`
        : '';

    // Production Date
    const prodDate = row.production_date
        ? frappe.format(row.production_date, { fieldtype: 'Date' })
        : '';

    // Finished Item
    const finishedItem = row.finished_item
        ? frappe.utils.escape_html(row.finished_item)
        : '';

    // Qty fields
    const fgPlannedQty        = format_qty_as_integer(row.fg_planned_qty);
    const actualQty           = format_qty_as_integer(row.actual_qty);
    const fgWeight            = format_qty_as_integer(row.fg_weight);
    const meltingWeight       = format_qty_as_integer(row.melting_weight);
    const finishPcs           = format_qty_as_integer(row.finish_pcs);
    const totalMissRollPcs    = format_qty_as_integer(row.total_miss_roll_pcs);
    const totalMissRollWeight = format_qty_as_integer(row.total_miss_roll_weight);
    const totalMissIngotPcs   = format_qty_as_integer(row.total_miss_ingot_pcs);
    const totalMissIngotWeight= format_qty_as_integer(row.total_miss_ingot_weight);
    const billetPcs           = format_qty_as_integer(row.billet_pcs);
    const totalRawMaterialPcs = format_qty_as_integer(row.total_raw_material_pcs);
    const missBilletPcs       = format_qty_as_integer(row.miss_billet_pcs);
    const missBilletWeight    = format_qty_as_integer(row.miss_billet_weight);
    const totalRMWeight       = format_qty_as_integer(
        (parseFloat(row.rm_consumption) || 0) + (parseFloat(row.miss_billet_weight) || 0)
    );
    const heatNo          = row.heat_no ? frappe.utils.escape_html(String(row.heat_no)) : '';
    const totalHrConsumed = format_number_with_decimals(row.total_hr_consumed);
    const rmConsumption   = format_qty_as_integer(row.rm_consumption);
    const fgLength        = row.fg_length ? frappe.utils.escape_html(String(row.fg_length)) : '';
    const rm              = row.rm ? frappe.utils.escape_html(row.rm) : '';
    const descriptionOfCuttingBillet = row.description_of_cutting_billet
        ? frappe.utils.escape_html(String(row.description_of_cutting_billet))
        : '';

    // Last column – percentage
    let lastColValue = '';
    if (tabId === 'rolled_production') {
        lastColValue = format_percentage(row.burning_loss);
    } else {
        lastColValue = format_percentage(row.wastage);
    }

    // ── Rolled Production ──
    if (tabId === 'rolled_production') {
        const burningLossVal = parseFloat(row.burning_loss) || 0;
        const rowBg = burningLossVal > 3.5 ? 'background:#ffe5e5;' : '';
        const tdHighlight = rowBg ? tdStyle + rowBg : tdStyle;
        const tdCol0H = tdCol0 + rowBg;
        const tdCol1H = tdCol1 + rowBg;

        const rmCategoryName = row.rm_category_name ? frappe.utils.escape_html(row.rm_category_name) : '';
        const finishedItemCategoryName = row.finished_item_category_name ? frappe.utils.escape_html(row.finished_item_category_name) : '';

        return `<tr style="border-bottom:1px solid #e9ecef;${rowBg}">
            <td style="${tdCol0H}">${ppLink}</td>
            <td style="${tdCol1H}">${prodDate}</td>
            <td style="${tdHighlight}">${rm}</td>
            <td style="${tdHighlight}">${rmCategoryName}</td>
            <td style="${tdHighlight}">${rmConsumption}</td>
            <td style="${tdHighlight}">${billetPcs}</td>
            <td style="${tdHighlight}">${descriptionOfCuttingBillet}</td>
            <td style="${tdHighlight}">${totalRawMaterialPcs}</td>
            <td style="${tdHighlight}">${totalRMWeight}</td>
            <td style="${tdHighlight}">${missBilletPcs}</td>
            <td style="${tdHighlight}">${missBilletWeight}</td>
            <td style="${tdHighlight} border-right:2px solid #dee2e6;">${heatNo}</td>
            <td style="${tdHighlight}">${finishedItem}</td>
            <td style="${tdHighlight}">${finishedItemCategoryName}</td>
            <td style="${tdHighlight}">${fgPlannedQty}</td>
            <td style="${tdHighlight}">${actualQty}</td>
            <td style="${tdHighlight}">${finishPcs}</td>
            <td style="${tdHighlight}">${fgLength}</td>
            <td style="${tdHighlight}">${totalMissRollPcs}</td>
            <td style="${tdHighlight}">${totalMissRollWeight}</td>
            <td style="${tdHighlight}">${totalMissIngotPcs}</td>
            <td style="${tdHighlight} border-right:2px solid #dee2e6;">${totalMissIngotWeight}</td>
            <td style="${tdHighlight}">${meltingWeight}</td>
            <td style="${tdHighlight}">${lastColValue}</td>
            <td style="${tdHighlight}">${totalHrConsumed}</td>
        </tr>`;
    }

    // ── Bend Weight Details ──
    if (tabId === 'bend_weight_details') {
        const id = row.id || row.name || '';
        const safeId = id ? frappe.utils.escape_html(String(id)) : '';
        const itemCode = row.item_code ? frappe.utils.escape_html(String(row.item_code)) : '';
        const bendCategoryName = row.category_name ? frappe.utils.escape_html(String(row.category_name)) : '';
        const bendWeight = format_number_with_decimals(row.bend_material_weight);

        return `<tr style="border-bottom:1px solid #e9ecef;">
            <td style="${tdCol0}">${safeId}</td>
            <td style="${tdCol1}">${itemCode}</td>
            <td style="${tdStyle}">${bendCategoryName}</td>
            <td style="${tdStyle}">${bendWeight}</td>
        </tr>`;
    }

    // ── Bright Production ──
    const machineName      = row.machine_name ? frappe.utils.escape_html(String(row.machine_name)) : '';
    const finishLength     = row.finish_length ? frappe.utils.escape_html(String(row.finish_length)) : '';
    const tolerance        = format_percentage(row.tolerance);
    const brightRmCategoryName = row.rm_category_name ? frappe.utils.escape_html(String(row.rm_category_name)) : '';
    const brightFiCategoryName = row.finished_item_category_name ? frappe.utils.escape_html(String(row.finished_item_category_name)) : '';

    return `<tr style="border-bottom:1px solid #e9ecef;">
        <td style="${tdCol0}">${ppLink}</td>
        <td style="${tdCol1}">${prodDate}</td>
        <td style="${tdStyle}">${rm}</td>
        <td style="${tdStyle}">${brightRmCategoryName}</td>
        <td style="${tdStyle}">${rmConsumption}</td>
        <td style="${tdStyle} border-right:2px solid #dee2e6;">${machineName}</td>
        <td style="${tdStyle}">${finishedItem}</td>
        <td style="${tdStyle}">${brightFiCategoryName}</td>
        <td style="${tdStyle}">${fgPlannedQty}</td>
        <td style="${tdStyle}">${actualQty}</td>
        <td style="${tdStyle}">${finishLength}</td>
        <td style="${tdStyle}">${tolerance}</td>
        <td style="${tdStyle}">${fgWeight}</td>
        <td style="${tdStyle}">${lastColValue}</td>
    </tr>`;
}

function getTableColumns(tabId) {
    if (tabId === 'rolled_production') {
        return [
            { label: __('Production Plan'), align: 'left' },
            { label: __('Production Date'), align: 'left' },
            { label: __('RM'), align: 'left' },
            { label: __('RM Category Name'), align: 'left' },
            { label: __('Actual RM Consumption'), align: 'left' },
            { label: __('Total Billet Pcs'), align: 'left' },
            { label: __('Description of Cutting Billet'), align: 'left' },
            { label: __('Total Raw Material Pcs'), align: 'left' },
            { label: __('Total RM Weight'), align: 'left' },
            { label: __('Miss Billet Pcs'), align: 'left' },
            { label: __('Miss Billet Weight'), align: 'left' },
            { label: __('Heat No'), align: 'left' },
            { label: __('Finished Item'), align: 'left' },
            { label: __('Finished Item Category Name'), align: 'left' },
            { label: __('FG Planned Qty'), align: 'left' },
            { label: __('Actual Qty'), align: 'left' },
            { label: __('Finish Pcs'), align: 'left' },
            { label: __('FG Length'), align: 'left' },
            { label: __('Total Miss Roll (Pcs)'), align: 'left' },
            { label: __('Total Miss Roll Weight'), align: 'left' },
            { label: __('Total Miss Ingot'), align: 'left' },
            { label: __('Total Miss Ingot / Billet Weight'), align: 'left' },
            { label: __('Melting Weight'), align: 'left' },
            { label: __('Burning Loss %'), align: 'left' },
            { label: __('Total Hr Consumed'), align: 'left' },
        ];
    }

    if (tabId === 'bend_weight_details') {
        return [
            { label: __('ID'), align: 'left' },
            { label: __('Item Code'), align: 'left' },
            { label: __('Category Name'), align: 'left' },
            { label: __('Bend Material Weight'), align: 'left' },
        ];
    }

    // bright_production
    return [
        { label: __('Production Plan'), align: 'left' },
        { label: __('Production Date'), align: 'left' },
        { label: __('RM'), align: 'left' },
        { label: __('RM Category Name'), align: 'left' },
        { label: __('Actual RM Consumption'), align: 'left' },
        { label: __('Machine Name'), align: 'left' },
        { label: __('Finished Item'), align: 'left' },
        { label: __('Finished Item Category Name'), align: 'left' },
        { label: __('FG Planned Qty'), align: 'left' },
        { label: __('Actual Qty'), align: 'left' },
        { label: __('Finish Length'), align: 'left' },
        { label: __('Tolerance'), align: 'left' },
        { label: __('Melting Weight'), align: 'left' },
        { label: __('Wastage %'), align: 'left' },
    ];
}

// ────────────────────────────────────────────────────────────────
// Export Helpers (Excel & PDF)
// ────────────────────────────────────────────────────────────────
function buildExportToolbar(state, tabId, columns, rows) {
    const $wrapper = $(`
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
            <div class="export-dropdown" style="position:relative;">
                <button type="button"
                        class="btn btn-sm"
                        style="background-color:#28a745;color:#fff;border:none;
                               padding:6px 14px;border-radius:4px;
                               display:flex;align-items:center;gap:6px;">
                    <span>${__('Export')}</span>
                    <span style="font-size:0.8rem;">▾</span>
                </button>
                <div class="export-menu"
                     style="display:none;position:absolute;right:0;top:100%;
                            background:#fff;border:1px solid #ced4da;
                            border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,0.15);
                            min-width:160px;z-index:10;">
                    <div class="export-option"
                         data-format="excel"
                         style="padding:8px 12px;cursor:pointer;font-size:0.9rem;">
                        ${__('Export to Excel')}
                    </div>
                    <div class="export-option"
                         data-format="pdf"
                         style="padding:8px 12px;cursor:pointer;font-size:0.9rem;">
                        ${__('Export to PDF')}
                    </div>
                </div>
            </div>
        </div>
    `);

    const $btn  = $wrapper.find('button');
    const $menu = $wrapper.find('.export-menu');

    $btn.on('click', (e) => {
        e.stopPropagation();
        $menu.toggle();
    });

    $menu.find('.export-option[data-format="excel"]').on('click', (e) => {
        e.stopPropagation();
        exportTableToExcel(state, tabId);
        $menu.hide();
    });

    $menu.find('.export-option[data-format="pdf"]').on('click', (e) => {
        e.stopPropagation();
        exportTableToPDF(tabId, columns, rows);
        $menu.hide();
    });

    // Hide dropdown when clicking outside
    $(document).on(`click.exportDropdown-${tabId}`, () => {
        $menu.hide();
    });

    return $wrapper;
}

function exportTableToExcel(state, tabId) {
    const filters = getFilters(state);

    const from_date = filters.from_date || '';
    const to_date = filters.to_date || (filters.from_date ? '' : frappe.datetime.get_today());

    const params = {
        tab_id: tabId,
        from_date: from_date,
        to_date: to_date,
        item_code: filters.item_code || '',
        production_plan: filters.production_plan || '',
        machine_name: filters.machine_name || '',
    };

    const query = Object.keys(params)
        .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(params[k] || '')}`)
        .join('&');

    const url = `/api/method/prakash_steel.api.production_dashboard.export_production_dashboard?${query}`;
    window.open(url, '_blank');
}

function exportTableToPDF(tabId, columns, rows) {
    if (!rows || !rows.length) {
        frappe.show_alert({ message: __('No data to export'), indicator: 'orange' });
        return;
    }

    const header = columns.map(c => frappe.utils.escape_html(c.label));
    const dataRows = rows.map(r => mapRowForExport(tabId, r).map(val =>
        frappe.utils.escape_html(val == null ? '' : String(val))
    ));

    const thead = `<tr>${header.map(h => `<th style="border:1px solid #000;padding:4px;">${h}</th>`).join('')}</tr>`;
    const tbody = dataRows.map(rowArr =>
        `<tr>${rowArr.map(v => `<td style="border:1px solid #000;padding:4px;">${v}</td>`).join('')}</tr>`
    ).join('');

    const html = `
        <html>
        <head>
            <title>${__('Production Dashboard Export')}</title>
        </head>
        <body>
            <h3>${__('Production Dashboard')} - ${__(tabId.replace(/_/g, ' '))}</h3>
            <table style="border-collapse:collapse;width:100%;font-size:11px;">
                <thead>${thead}</thead>
                <tbody>${tbody}</tbody>
            </table>
        </body>
        </html>
    `;

    const win = window.open('', '_blank');
    if (!win) {
        frappe.msgprint(__('Please allow popups to export PDF.'));
        return;
    }
    win.document.open();
    win.document.write(html);
    win.document.close();
    win.focus();
    win.print();
}

function buildCSVContent(rows) {
    const escapeCell = (value) => {
        if (value === undefined || value === null) return '';
        const str = String(value);
        if (/[",\n]/.test(str)) {
            return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
    };

    return rows.map(rowArr => rowArr.map(escapeCell).join(',')).join('\n');
}

function mapRowForExport(tabId, row) {
    if (tabId === 'rolled_production') {
        return [
            row.production_plan || '',
            row.production_date
                ? frappe.format(row.production_date, { fieldtype: 'Date' })
                : '',
            row.rm || '',
            row.rm_category_name || '',
            row.rm_consumption || 0,
            row.billet_pcs || 0,
            row.description_of_cutting_billet || '',
            row.total_raw_material_pcs || 0,
            (row.rm_consumption || 0) + (row.miss_billet_weight || 0),
            row.miss_billet_pcs || 0,
            row.miss_billet_weight || 0,
            row.heat_no || '',
            row.finished_item || '',
            row.finished_item_category_name || '',
            row.fg_planned_qty || 0,
            row.actual_qty || 0,
            row.finish_pcs || 0,
            row.fg_length || '',
            row.total_miss_roll_pcs || 0,
            row.total_miss_roll_weight || 0,
            row.total_miss_ingot_pcs || 0,
            row.total_miss_ingot_weight || 0,
            row.melting_weight || 0,
            row.burning_loss || 0,
            row.total_hr_consumed || 0,
        ];
    }

    if (tabId === 'bend_weight_details') {
        return [
            row.id || row.name || '',
            row.item_code || '',
            row.category_name || '',
            row.bend_material_weight || 0,
        ];
    }

    // bright_production
    return [
        row.production_plan || '',
        row.production_date
            ? frappe.format(row.production_date, { fieldtype: 'Date' })
            : '',
        row.rm || '',
        row.rm_category_name || '',
        row.rm_consumption || 0,
        row.machine_name || '',
        row.finished_item || '',
        row.finished_item_category_name || '',
        row.fg_planned_qty || 0,
        row.actual_qty || 0,
        row.finish_length || '',
        row.tolerance || 0,
        row.wastage || 0,
    ];
}