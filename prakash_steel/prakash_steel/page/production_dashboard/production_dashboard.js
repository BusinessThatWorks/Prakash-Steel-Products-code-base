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

    $filterControls
        .append($fromDateWrap)
        .append($toDateWrap)
        .append($itemWrap)
        .append($ppWrap);

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

    // ── Style inputs ──
    setTimeout(() => {
        [state.controls.from_date, state.controls.to_date,
         state.controls.item_code, state.controls.production_plan].forEach(c => {
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
    } else {
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
        const title = tabId === 'rolled_production'
            ? __('Rolled Production Details')
            : __('Bright Production Details');

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
     state.controls.item_code, state.controls.production_plan].forEach(c => {
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

    // ── Refresh button ──
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

    const apiMethod = tabId === 'rolled_production'
        ? 'prakash_steel.api.production_dashboard.get_rolled_production_data'
        : 'prakash_steel.api.production_dashboard.get_bright_production_data';

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

    // Use teal and light pink for Rolled Production, red and green for Bright Production
    const gradientClasses = tabId === 'rolled_production'
        ? ['card-teal', 'card-pink']
        : ['card-red', 'card-green'];

    const cards = [
        {
            value: totals.total_production,
            label: __('Total Production (kg)'),
            gradientClass: gradientClasses[0],
            description: __('Sum of Qty across all rows'),
        },
        {
            value: totals.rm_consumption,
            label: __('RM Consumption'),
            gradientClass: gradientClasses[1],
            description: __('Sum of RM Consumption across all rows'),
        },
    ];

    cards.forEach(card => {
        $container.append(buildCardHtml(card));
    });
}

function buildCardHtml(card) {
    const raw = card.value;
    const display = (raw === undefined || raw === null || raw === '')
        ? '--'
        : format_number(raw, null, 2);

    const gradientClass = card.gradientClass || 'card-blue';
    const gradient = getGradientStyle(gradientClass);

    const desc = card.description
        ? `<div style="font-size:0.85rem;color:#000;margin-top:8px;opacity:0.7;">${frappe.utils.escape_html(card.description)}</div>`
        : '';

    return $(`
        <div class="number-card ${gradientClass}"
             style="background:${gradient} !important;background-image:${gradient} !important;
                    border-radius:12px;padding:18px;
                    box-shadow:none;
                    position:relative;overflow:hidden;
                    transition:transform .2s,box-shadow .2s;
                    color:#000;border:none;">
            <div style="text-align:center;">
                <div style="font-size:2.4rem;font-weight:700;color:#000;
                            margin-bottom:8px;line-height:1.1;">${display}</div>
                <div style="font-size:1rem;color:#000;font-weight:500;opacity:0.95;">
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

    // ── Header ──
    const thStyle = 'background:#e4d5b9;padding:12px;font-weight:600;color:#000000;'
        + 'border-bottom:2px solid #d4c5a9;white-space:nowrap;text-align:center !important;';

    const headerHtml = columns.map(c =>
        `<th style="${thStyle}">${c.label}</th>`
    ).join('');

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
        <div style="width:100%;margin-bottom:30px;overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;background:#fff;
                          border-radius:6px;overflow:hidden;
                          box-shadow:0 1px 3px rgba(0,0,0,.1);min-width:1000px;">
                <thead><tr>${headerHtml}</tr></thead>
                <tbody>${bodyHtml}</tbody>
            </table>
        </div>`);

    $container.append($table);
}

function buildTableRow(tabId, row) {
    const tdStyle = 'padding:12px;border-bottom:1px solid #e9ecef;color:#495057;text-align:center !important;';

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

    // Numeric fields – use format_number to get plain text (no wrapper HTML)
    const fgPlannedQty = format_number(row.fg_planned_qty || 0, null, 2);
    const actualQty    = format_number(row.actual_qty || 0, null, 2);
    const fgLength     = format_number(row.fg_length || 0, null, 2);
    const rmConsumption = format_number(row.rm_consumption || 0, null, 2);

    // RM
    const rm = row.rm ? frappe.utils.escape_html(row.rm) : '';

    // Last column differs per tab
    let lastColValue = '';
    if (tabId === 'rolled_production') {
        lastColValue = format_number(row.burning_loss || 0, null, 2);
    } else {
        lastColValue = format_number(row.wastage || 0, null, 2);
    }

    return `<tr style="border-bottom:1px solid #e9ecef;">
        <td style="${tdStyle}">${ppLink}</td>
        <td style="${tdStyle}">${prodDate}</td>
        <td style="${tdStyle}">${finishedItem}</td>
        <td style="${tdStyle}">${fgPlannedQty}</td>
        <td style="${tdStyle}">${actualQty}</td>
        <td style="${tdStyle}">${fgLength}</td>
        <td style="${tdStyle}">${rm}</td>
        <td style="${tdStyle}">${rmConsumption}</td>
        <td style="${tdStyle}">${lastColValue}</td>
    </tr>`;
}

function getTableColumns(tabId) {
    if (tabId === 'rolled_production') {
        return [
            { label: __('Production Plan'), align: 'left' },
            { label: __('Production Date'), align: 'left' },
            { label: __('Finished Item'), align: 'left' },
            { label: __('FG Planned Qty'), align: 'left' },
            { label: __('Actual Qty'), align: 'left' },
            { label: __('FG Length'), align: 'left' },
            { label: __('RM'), align: 'left' },
            { label: __('RM Consumption'), align: 'left' },
            { label: __('Burning Loss %'), align: 'left' },
        ];
    }
    // bright_production
    return [
        { label: __('Production Plan'), align: 'left' },
        { label: __('Production Date'), align: 'left' },
        { label: __('Finished Item'), align: 'left' },
        { label: __('FG Planned Qty'), align: 'left' },
        { label: __('Actual Qty'), align: 'left' },
        { label: __('FG Length'), align: 'left' },
        { label: __('RM'), align: 'left' },
        { label: __('RM Consumption'), align: 'left' },
        { label: __('Wastage %'), align: 'left' },
    ];
}
