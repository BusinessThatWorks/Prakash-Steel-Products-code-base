frappe.pages["daily-po-recommendation"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Daily PO Recommendation",
		single_column: true,
	});

	new DailyPORecommendation(page);
};

class DailyPORecommendation {
	constructor(page) {
		this.page = page;
		this.active_sku_tab = "BBMTA";
		this.data_cache = {};

		this.render_layout();
		this.setup_controls();
	}

	render_layout() {
		const $body = $(this.page.body);
		$body.empty();

		// SKU colour palette — each tab gets its own accent colour
		const sku_colors = {
			BBMTA: "#4361ee", RBMTA: "#7209b7", BOTA: "#f72585",
			PTA:   "#3a0ca3", TRMTA: "#480ca8",
			BBMTO: "#0077b6", RBMTO: "#00b4d8", BOTO: "#06d6a0",
			PTO:   "#f4a261", TRMTO: "#e76f51",
		};

		$body.append(`
			<style>
				.daily-po-page .sku-tab-link {
					font-size: 12px;
					font-weight: 600;
					padding: 5px 14px;
					border-radius: 20px !important;
					color: #495057;
					background: #f1f3f5;
					border: 2px solid transparent;
					transition: all 0.2s;
				}
				.daily-po-page .sku-tab-link:hover {
					background: #e9ecef;
					color: #212529;
				}
				${this.get_sku_types().map(sku => `
				.daily-po-page .sku-tab-link[data-sku="${sku}"].active {
					background: ${sku_colors[sku]};
					color: #fff !important;
					border-color: ${sku_colors[sku]};
					box-shadow: 0 3px 8px ${sku_colors[sku]}55;
				}
				`).join("")}
				.daily-po-page .main-tab-link {
					font-weight: 600;
					font-size: 13px;
					color: #495057;
					border-radius: 6px 6px 0 0 !important;
					padding: 8px 20px;
				}
				.daily-po-page .main-tab-link.active {
					color: #4361ee !important;
					border-color: #d1d8dd #d1d8dd #fff !important;
					background: #fff !important;
				}
				.daily-po-page .export-btn {
					background: linear-gradient(135deg, #1d7641, #28a745);
					color: #fff !important;
					border: none;
					border-radius: 6px;
					font-weight: 600;
					font-size: 12px;
					box-shadow: 0 2px 6px #28a74540;
					transition: opacity 0.2s;
				}
				.daily-po-page .export-btn:hover { opacity: 0.88; color: #fff; }
				.daily-po-page .apply-btn {
					background: linear-gradient(135deg, #2563eb, #4361ee) !important;
					border: none !important;
					border-radius: 6px !important;
					font-weight: 600 !important;
					box-shadow: 0 2px 6px #4361ee44 !important;
				}
				.daily-po-page thead th {
					background: linear-gradient(135deg, #f0f4ff, #e8ecf8) !important;
					color: #2d3a8c;
					font-weight: 700;
					position: sticky;
					top: 0;
					z-index: 2;
				}
				.daily-po-page tbody tr:hover { background: #f5f8ff !important; }
				.daily-po-page .dt-wrapper .dt-scrollable {
					max-height: calc(100vh - 340px);
				}
			</style>

			<div class="daily-po-page" style="padding: 15px;">

				<!-- Filter Bar -->
				<div class="filter-bar" style="
					display: flex;
					align-items: center;
					gap: 16px;
					padding: 12px 20px;
					background: linear-gradient(135deg, #eef2ff, #f8f0fc);
					border: 1px solid #c5cdf8;
					border-radius: 10px;
					margin-bottom: 16px;
					flex-wrap: wrap;
					box-shadow: 0 2px 8px #4361ee18;
				">
					<div style="display:flex; align-items:center; gap:7px; padding-right:12px; border-right:2px solid #c5cdf8;">
						<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4361ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
						<span style="font-size:12px; font-weight:700; color:#4361ee; white-space:nowrap;">PO Snapshot Filters</span>
					</div>
					<div style="display:flex; flex-direction:column; gap:3px;">
						<label style="font-size:11px; font-weight:700; color:#4361ee; margin:0; letter-spacing:0.3px;">SNAPSHOT DATE <span style="color:#e63946;">*</span></label>
						<div class="snapshot-date-control" style="min-width:160px;"></div>
					</div>
					<div style="display:flex; flex-direction:column; gap:3px;">
						<label style="font-size:11px; font-weight:700; color:#7209b7; margin:0; letter-spacing:0.3px;">ITEM CODE</label>
						<div class="item-code-control" style="min-width:200px;"></div>
					</div>
					<button class="btn btn-primary btn-sm apply-btn" style="height:32px; padding:0 20px; margin-top:14px;">
						Apply
					</button>
				</div>

				<!-- Main Tabs -->
				<ul class="nav nav-tabs main-tabs" style="margin-bottom:0; border-bottom: 2px solid #c5cdf8;">
					<li class="nav-item">
						<a class="nav-link active main-tab-link" data-tab="po_recommendation" href="#">
							📊 PO Recommendation Report
						</a>
					</li>
				</ul>

				<!-- Main Tab Content -->
				<div class="main-tab-content" style="border:1px solid #c5cdf8; border-top:none; padding:16px; background:#fff; border-radius:0 0 10px 10px; box-shadow:0 4px 12px #4361ee0f;">

					<!-- PO Recommendation Tab -->
					<div class="main-tab-pane active" data-pane="po_recommendation">

						<!-- SKU Sub-tabs + Export button -->
						<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
							<ul class="nav nav-pills sku-tabs" style="flex-wrap:wrap; gap:6px; margin:0;">
								${this.get_sku_types().map((sku, i) => `
									<li class="nav-item">
										<a class="nav-link sku-tab-link ${i === 0 ? "active" : ""}"
										   data-sku="${sku}" href="#">
											${sku}
										</a>
									</li>
								`).join("")}
							</ul>
							<button class="btn btn-sm export-btn" style="display:flex; align-items:center; gap:6px; white-space:nowrap; padding:5px 14px;">
								<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
								Export Excel
							</button>
						</div>

						<!-- Table Area -->
						<div class="sku-table-wrapper">
							<div class="sku-loading" style="display:none; text-align:center; padding:50px; color:#4361ee;">
								<div style="font-size:28px; margin-bottom:8px;">⏳</div>
								<span style="font-size:13px; font-weight:600;">Loading data...</span>
							</div>
							<div class="sku-no-data" style="display:none; text-align:center; padding:50px; color:#8d99a6;">
								<div style="font-size:32px; margin-bottom:8px;">📭</div>
								<span style="font-size:13px;">No data found for selected date.</span>
							</div>
							<div class="sku-table-area"></div>
						</div>
					</div>

				</div>
			</div>
		`);

		this.bind_tab_events();
	}

	setup_controls() {
		const $body = $(this.page.body);

		// Date control
		this.date_control = frappe.ui.form.make_control({
			df: {
				fieldname: "snapshot_date",
				fieldtype: "Date",
				placeholder: "Select Date",
			},
			parent: $body.find(".snapshot-date-control")[0],
			render_input: true,
		});
		const yesterday = frappe.datetime.add_days(frappe.datetime.get_today(), -1);
		this.date_control.set_value(yesterday);
		// Remove the label Frappe auto-adds (we have our own)
		$body.find(".snapshot-date-control .control-label").hide();

		// Auto-load once control value is set
		setTimeout(() => this.load_data(false), 100);

		// Item Code (Link) control
		this.item_control = frappe.ui.form.make_control({
			df: {
				fieldname: "item_code",
				fieldtype: "Link",
				options: "Item",
				placeholder: "All Items",
			},
			parent: $body.find(".item-code-control")[0],
			render_input: true,
		});
		$body.find(".item-code-control .control-label").hide();

		// Apply button
		$body.find(".apply-btn").on("click", () => {
			this.data_cache = {};
			this.load_data(true);
		});
	}

	get_sku_types() {
		return ["BBMTA", "RBMTA", "BOTA", "PTA", "TRMTA", "BBMTO", "RBMTO", "BOTO", "PTO", "TRMTO"];
	}

	bind_tab_events() {
		const $body = $(this.page.body);

		// Main tab click
		$body.on("click", ".main-tab-link", (e) => {
			e.preventDefault();
			const tab = $(e.currentTarget).data("tab");
			$body.find(".main-tab-link").removeClass("active");
			$(e.currentTarget).addClass("active");
			$body.find(".main-tab-pane").removeClass("active").hide();
			$body.find(`.main-tab-pane[data-pane="${tab}"]`).addClass("active").show();
		});

		// SKU sub-tab click
		$body.on("click", ".sku-tab-link", (e) => {
			e.preventDefault();
			const sku = $(e.currentTarget).data("sku");
			$body.find(".sku-tab-link").removeClass("active");
			$(e.currentTarget).addClass("active");
			this.active_sku_tab = sku;
			this.render_table(sku);
		});

		// Export button
		$body.on("click", ".export-btn", () => {
			this.export_to_excel();
		});
	}

	get_filter_values() {
		return {
			snapshot_date: this.date_control.get_value(),
			item_code: this.item_control.get_value() || null,
		};
	}

	load_data(show_error = false) {
		const { snapshot_date, item_code } = this.get_filter_values();
		if (!snapshot_date) {
			if (show_error) frappe.msgprint(__("Please select a Snapshot Date"));
			return;
		}
		this.fetch_and_render(this.active_sku_tab, snapshot_date, item_code);
	}

	fetch_and_render(sku_type, snapshot_date, item_code) {
		const cache_key = `${sku_type}__${snapshot_date}__${item_code || ""}`;
		if (this.data_cache[cache_key]) {
			this.render_table(sku_type, this.data_cache[cache_key]);
			return;
		}

		this.show_loading(true);

		frappe.call({
			method: "prakash_steel.po_recommendation_history.page.daily_po_recommendation.daily_po_recommendation.get_sku_data",
			args: { sku_type, snapshot_date, item_code },
			callback: (r) => {
				this.show_loading(false);
				if (r.message) {
					this.data_cache[cache_key] = r.message;
					this.render_table(sku_type, r.message);
				}
			},
			error: () => {
				this.show_loading(false);
				this.show_no_data();
			},
		});
	}

	fmt_date(iso) {
		// "2026-04-13" → "13-04-26"
		if (!iso) return iso;
		const [y, m, d] = iso.split("-");
		return `${d}-${m}-${y.slice(2)}`;
	}

	render_table(sku_type, result) {
		const { snapshot_date, item_code } = this.get_filter_values();

		if (!result) {
			const cache_key = `${sku_type}__${snapshot_date}__${item_code || ""}`;
			if (this.data_cache[cache_key]) {
				result = this.data_cache[cache_key];
			} else {
				this.fetch_and_render(sku_type, snapshot_date, item_code);
				return;
			}
		}

		const $wrapper = $(this.page.body).find(".sku-table-area");
		const $no_data = $(this.page.body).find(".sku-no-data");
		$no_data.hide();

		if (!result.data || result.data.length === 0) {
			// destroy any existing datatable
			if (this.datatable) { this.datatable.destroy(); this.datatable = null; }
			$wrapper.empty();
			$no_data.show();
			return;
		}

		const sku_colors = {
			BBMTA: "#4361ee", RBMTA: "#7209b7", BOTA: "#f72585",
			PTA:   "#3a0ca3", TRMTA: "#480ca8",
			BBMTO: "#0077b6", RBMTO: "#00b4d8", BOTO: "#06d6a0",
			PTO:   "#f4a261", TRMTO: "#e76f51",
		};
		const accent = sku_colors[sku_type] || "#4361ee";

		const colour_map = {
			BLACK:  { bg: "#000000", text: "#FFFFFF" },
			RED:    { bg: "#FF0000", text: "#FFFFFF" },
			YELLOW: { bg: "#FFFF00", text: "#000000" },
			GREEN:  { bg: "#00C853", text: "#FFFFFF" },
			WHITE:  { bg: "#F5F5F5", text: "#000000" },
		};

		// Build info bar + datatable container
		$wrapper.html(`
			<div style="
				margin-bottom:8px;
				padding:8px 14px;
				background:linear-gradient(135deg, ${accent}18, ${accent}08);
				border-left:4px solid ${accent};
				border-radius:0 6px 6px 0;
				display:flex; align-items:center; gap:10px;
				font-size:12px;
			">
				<span style="font-weight:700; color:${accent}; font-size:13px;">${sku_type}</span>
				<span style="color:#6c757d;">
					${result.data.length} record${result.data.length !== 1 ? "s" : ""}
					&nbsp;·&nbsp; Snapshot Date: <strong>${this.fmt_date(snapshot_date)}</strong>
				</span>
			</div>
			<div class="dt-wrapper"></div>
		`);

		// Prepare columns for Frappe DataTable
		const dt_columns = result.columns.map(col => {
			const base = {
				id: col.fieldname,
				name: col.label,
				width: col.width || 120,
				editable: false,
				resizable: true,
			};

			if (col.fieldname === "on_hand_colour") {
				base.format = (value) => {
					if (!value) return "";
					const c = colour_map[value] || {};
					return `<span style="display:inline-block;background:${c.bg || ""};color:${c.text || ""};padding:2px 8px;border-radius:10px;font-weight:700;font-size:11px;">${value}</span>`;
				};
			} else if (col.fieldname === "item_code") {
				base.format = (value) => {
					if (!value) return "";
					return `<a href="/app/item/${encodeURIComponent(value)}" style="color:#4361ee;">${value}</a>`;
				};
			} else if (col.fieldtype === "Float") {
				base.format = (value) => {
					if (value === null || value === undefined || value === "") return "";
					return frappe.format(value, { fieldtype: "Float" });
				};
			}

			return base;
		});

		// Prepare data rows as objects keyed by fieldname
		const dt_data = result.data.map(row => {
			const obj = {};
			result.columns.forEach(col => {
				obj[col.fieldname] = row[col.fieldname] ?? "";
			});
			return obj;
		});

		// Destroy previous instance if any
		if (this.datatable) { this.datatable.destroy(); this.datatable = null; }

		const container = $wrapper.find(".dt-wrapper")[0];
		this.datatable = new DataTable(container, {
			columns: dt_columns,
			data: dt_data,
			inlineFilters: true,
			layout: "fixed",
			cellHeight: 32,
			serialNoColumn: false,
			checkboxColumn: false,
			language: frappe.boot.lang,
			translations: frappe.utils.datatable.get_translations(),
			noDataMessage: __("No data found"),
		});
	}

	show_loading(state) {
		const $loading = $(this.page.body).find(".sku-loading");
		const $area = $(this.page.body).find(".sku-table-area");
		if (state) {
			$loading.show();
			$area.empty();
		} else {
			$loading.hide();
		}
	}

	show_no_data() {
		$(this.page.body).find(".sku-no-data").show();
		$(this.page.body).find(".sku-table-area").empty();
	}

	export_to_excel() {
		const { snapshot_date, item_code } = this.get_filter_values();
		if (!snapshot_date) {
			frappe.msgprint(__("Please select a Snapshot Date first"));
			return;
		}

		const sku_type = this.active_sku_tab;
		const $btn = $(this.page.body).find(".export-btn");
		$btn.prop("disabled", true).text("Exporting...");

		frappe.call({
			method: "prakash_steel.po_recommendation_history.page.daily_po_recommendation.daily_po_recommendation.export_sku_xlsx",
			args: { sku_type, snapshot_date, item_code },
			callback: (r) => {
				$btn.prop("disabled", false).html(`
					<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
					Export Excel
				`);
				if (!r.message) return;

				const { content, filename } = r.message;
				const fmt_name = filename.replace(
					/(\d{4})-(\d{2})-(\d{2})\.xlsx$/,
					(_, y, m, d) => `${d}-${m}-${y.slice(2)}.xlsx`
				);

				const bytes = Uint8Array.from(atob(content), c => c.charCodeAt(0));
				const blob = new Blob([bytes], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
				const url = URL.createObjectURL(blob);
				const link = document.createElement("a");
				link.href = url;
				link.download = fmt_name;
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
				URL.revokeObjectURL(url);
			},
			error: () => {
				$btn.prop("disabled", false).html(`
					<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
					Export Excel
				`);
			},
		});
	}
}
