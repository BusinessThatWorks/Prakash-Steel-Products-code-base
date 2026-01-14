// Prakash Steel Planning Dashboard
// Shows:
// - On Hand Status pies for SKU types (BBMTA, RBMTA, BOTA, RMTA, PTA)
// - Pending SO Status pie (by order_status colour)
// - Open PO Status pie (currently all BLACK)

frappe.pages['prakash-steel-planni'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Prakash Steel Planning Dashboard',
		single_column: true,
	});

	// Main container
	const $container = $(`
		<div class="planning-dashboard" style="padding: 20px;">
			<div class="charts-grid" style="
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
				gap: 24px;
			"></div>
		</div>
	`);

	page.main.empty();
	page.main.append($container);

	const $chartsContainer = $container.find('.charts-grid');

	page.set_indicator(__('Loading chart data...'), 'blue');

	const afterChartReady = () => load_all_charts(page, $chartsContainer);

	// Ensure Chart.js is available
	if (typeof Chart === 'undefined') {
		frappe.require('https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js', afterChartReady);
	} else {
		afterChartReady();
	}
};

function load_all_charts(page, $chartsContainer) {
	const colorMap = getColorMap();

	Promise.all([
		new Promise((resolve, reject) => {
			frappe.call({
				method: 'prakash_steel.prakash_steel.page.prakash_steel_planni.prakash_steel_planni.get_sku_type_on_hand_status',
				args: { filters: {} },
				callback: resolve,
				error: reject,
			});
		}),
		new Promise((resolve, reject) => {
			frappe.call({
				method: 'prakash_steel.prakash_steel.page.prakash_steel_planni.prakash_steel_planni.get_pending_so_status',
				callback: resolve,
				error: reject,
			});
		}),
		new Promise((resolve, reject) => {
			frappe.call({
				method: 'prakash_steel.prakash_steel.page.prakash_steel_planni.prakash_steel_planni.get_open_po_status',
				callback: resolve,
				error: reject,
			});
		}),
	])
		.then(([skuRes, pendingSoRes, openPoRes]) => {
			page.clear_indicator();

			// 1) SKU type pies
			if (skuRes && skuRes.message) {
				const skuData = skuRes.message;
				const skuTypes = ['BBMTA', 'RBMTA', 'BOTA', 'RMTA', 'PTA'];

				skuTypes.forEach((sku) => {
					if (skuData[sku] && skuData[sku].colours && skuData[sku].colours.length) {
						const $card = createChartCard(sku, skuData[sku], colorMap);
						$chartsContainer.append($card);
						renderPieChart(sku, skuData[sku], colorMap);
					}
				});
			}

			// 2) Pending SO Status pie
			if (pendingSoRes && pendingSoRes.message && pendingSoRes.message.colours && pendingSoRes.message.colours.length) {
				const $card = createChartCard('Pending SO Status', pendingSoRes.message, colorMap);
				$chartsContainer.append($card);
				renderPieChart('Pending SO Status', pendingSoRes.message, colorMap);
			}

			// 3) Open PO Status pie (all black for now)
			if (openPoRes && openPoRes.message) {
				const $card = createChartCard('Open PO Status', openPoRes.message, colorMap);
				$chartsContainer.append($card);
				renderPieChart('Open PO Status', openPoRes.message, colorMap);
			}

			if ($chartsContainer.children().length === 0) {
				$chartsContainer.append(`
					<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #7f8c8d;">
						<i class="fa fa-info-circle" style="font-size: 2rem; margin-bottom: 12px;"></i>
						<div>${__('No data available')}</div>
					</div>
				`);
			}
		})
		.catch((err) => {
			console.error('Error loading planning dashboard charts:', err);
			page.clear_indicator();
			$chartsContainer.append(`
				<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #e74c3c;">
					<i class="fa fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 12px;"></i>
					<div>${__('Error loading data')}</div>
				</div>
			`);
		});
}

function getColorMap() {
	return {
		BLACK: '#000000',
		RED: '#ff0000',
		YELLOW: '#ffff99',
		GREEN: '#4dff88',
		WHITE: '#ffffff',
	};
}

function createChartCard(key, data, colorMap) {
	const title = key.includes('Status') ? key : `${key} On Hand Status`;
	const chartId = key.replace(/\s+/g, '-');

	const $card = $(`
		<div class="chart-card" style="
			background:#fff;
			border-radius:12px;
			padding:24px;
			box-shadow:0 4px 12px rgba(0,0,0,0.1);
		">
			<h3 style="
				margin:0 0 20px 0;
				font-size:1.25rem;
				font-weight:600;
				color:#2c3e50;
				text-align:center;
			">${title}</h3>
			<div style="position:relative;height:300px;margin-bottom:20px;">
				<canvas id="chart-${chartId}" style="max-height:300px;"></canvas>
			</div>
			<div class="chart-legend-${chartId}" style="
				display:flex;
				flex-wrap:wrap;
				gap:12px;
				justify-content:center;
				margin-top:16px;
			"></div>
		</div>
	`);

	const $legend = $card.find(`.chart-legend-${chartId}`);
	if (data.colours && data.colours.length) {
		data.colours.forEach((c) => {
			const $item = $(`
				<div style="
					display:flex;
					align-items:center;
					gap:8px;
					padding:8px 12px;
					background:#f8f9fa;
					border-radius:6px;
					border:2px solid ${colorMap[c.name] || '#ccc'};
				">
					<div style="
						width:20px;
						height:20px;
						background:${colorMap[c.name] || '#ccc'};
						border-radius:4px;
						border:1px solid #ddd;
					"></div>
					<span style="font-weight:600;color:#2c3e50;">${c.name}:</span>
					<span style="color:#495057;">${c.count}</span>
					<span style="color:#7f8c8d;font-size:0.9rem;">(${c.percentage}%)</span>
				</div>
			`);
			$legend.append($item);
		});
	}

	return $card;
}

function renderPieChart(key, data, colorMap) {
	const chartId = key.replace(/\s+/g, '-');
	const canvas = document.getElementById(`chart-${chartId}`);
	if (!canvas || !data || !data.colours) return;

	if (typeof Chart === 'undefined') {
		console.warn('Chart.js not available');
		return;
	}

	const ctx = canvas.getContext('2d');
	const labels = data.colours.map((c) => c.name);
	const values = data.colours.map((c) => c.count);
	const colors = data.colours.map((c) => colorMap[c.name] || '#ccc');

	if (window[`chart_${chartId}`]) {
		window[`chart_${chartId}`].destroy();
	}

	window[`chart_${chartId}`] = new Chart(ctx, {
		type: 'pie',
		data: {
			labels,
			datasets: [
				{
					data: values,
					backgroundColor: colors,
					borderColor: '#fff',
					borderWidth: 2,
				},
			],
		},
		options: {
			responsive: true,
			maintainAspectRatio: true,
			plugins: {
				legend: { display: false },
				tooltip: {
					callbacks: {
						label: (ctx) => {
							const label = ctx.label || '';
							const value = ctx.parsed || 0;
							const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
							const pct = total ? ((value / total) * 100).toFixed(2) : '0.00';
							return `${label}: ${value} (${pct}%)`;
						},
					},
				},
			},
		},
	});
}








