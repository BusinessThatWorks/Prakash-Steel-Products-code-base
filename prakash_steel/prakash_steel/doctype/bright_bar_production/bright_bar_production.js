// Copyright (c) 2026, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bright Bar Production", {
	refresh(frm) {
		if (typeof frm.doc.production_plan === "string" && frm.doc.production_plan) {
			load_raw_material_options_from_production_plan(frm, null);
		}
	},

	production_plan: function (frm) {
		if (typeof frm.doc.production_plan !== "string" || !frm.doc.production_plan) {
			frm.set_df_property("raw_material", "options", "");
			frm.refresh_field("raw_material");
			return;
		}
		load_raw_material_options_from_production_plan(frm, null);
	}
});

function load_raw_material_options_from_production_plan(frm, callback) {
	if (typeof frm.doc.production_plan !== "string" || !frm.doc.production_plan) {
		if (callback) callback();
		return;
	}

	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Production Plan",
			name: frm.doc.production_plan
		},
		callback: function (r) {
			console.log("📦 Full frappe.call response:", r);

			if (!r.message) {
				console.log("❌ No document returned");
				if (callback) callback();
				return;
			}

			let pp = r.message;
			console.log("📄 Production Plan Doc:", pp);

			if (!pp.mr_items) {
				console.log("❌ mr_items not found in Production Plan");
				if (callback) callback();
				return;
			}

			console.log("📋 mr_items rows count:", pp.mr_items.length);

			let item_codes = [];

			pp.mr_items.forEach((row, index) => {
				console.log(`➡️ Row ${index}:`, row);

				if (row.item_code) {
					item_codes.push(row.item_code);
					console.log("➕ item_code added:", row.item_code);
				} else {
					console.log("⚠️ item_code missing in row", index);
				}
			});

			console.log("🧾 Final item_codes array:", item_codes);

			if (item_codes.length === 0) {
				console.log("❌ No item codes collected");
				if (callback) callback();
				return;
			}

			// Remove duplicates
			item_codes = [...new Set(item_codes)];
			console.log("🧹 Unique item_codes:", item_codes);

			// Set the options
			frm.set_df_property(
				"raw_material",
				"options",
				item_codes.join("\n")
			);

			console.log("✅ raw_material options set");

			frm.refresh_field("raw_material");
			
			if (callback) {
				console.log("✅ Calling callback function");
				callback();
			}
		}
	});
}

// Populate finished_good from Production Plan po_items
frappe.ui.form.on("Bright Bar Production", {
	refresh(frm) {
		if (typeof frm.doc.production_plan === "string" && frm.doc.production_plan) {
			load_finished_good_options_from_production_plan(frm, null);
		}
	},

	production_plan(frm) {
		if (typeof frm.doc.production_plan !== "string" || !frm.doc.production_plan) {
			frm.set_df_property("finished_good", "options", "");
			frm.refresh_field("finished_good");
			return;
		}
		load_finished_good_options_from_production_plan(frm, null);
	}
});

function load_finished_good_options_from_production_plan(frm, callback) {
	if (typeof frm.doc.production_plan !== "string" || !frm.doc.production_plan) {
		if (callback) callback();
		return;
	}

	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Production Plan",
			name: frm.doc.production_plan
		},
		callback(r) {
			console.log("📦 Full frappe.call response (finished_good):", r);

			if (!r.message) {
				console.log("❌ No document returned");
				if (callback) callback();
				return;
			}

			let pp = r.message;
			console.log("📄 Production Plan Doc:", pp);

			if (!pp.po_items) {
				console.log("❌ po_items not found in Production Plan");
				if (callback) callback();
				return;
			}

			console.log("📋 po_items rows count:", pp.po_items.length);

			let item_codes = [];

			pp.po_items.forEach((row, index) => {
				console.log(`➡️ Row ${index}:`, row);

				if (row.item_code) {
					item_codes.push(row.item_code);
					console.log("➕ item_code added:", row.item_code);
				} else {
					console.log("⚠️ item_code missing in row", index);
				}
			});

			console.log("🧾 Final item_codes array (finished_good):", item_codes);

			if (item_codes.length === 0) {
				console.log("❌ No item codes collected");
				if (callback) callback();
				return;
			}

			// Remove duplicates
			item_codes = [...new Set(item_codes)];
			console.log("🧹 Unique item_codes (finished_good):", item_codes);

			frm.set_df_property(
				"finished_good",
				"options",
				item_codes.join("\n")
			);

			console.log("✅ finished_good options set");

			frm.refresh_field("finished_good");

			if (callback) {
				console.log("✅ Calling callback function (finished_good)");
				callback();
			}
		}
	});
}

// Populate `finished` and `material` from Production Planning FG Table
frappe.ui.form.on("Bright Bar Production", {
	refresh(frm) {
		if (frm.doc.production_planning) {
			load_options_from_production_planning(frm);
		}
	},

	production_planning(frm) {
		if (!frm.doc.production_planning) {
			frm.set_df_property("finished", "options", "");
			frm.set_df_property("material", "options", "");
			frm.refresh_field("finished");
			frm.refresh_field("material");
			return;
		}
		load_options_from_production_planning(frm);
	}
});

function load_options_from_production_planning(frm) {
	if (!frm.doc.production_planning) return;

	frappe.call({
		method: "prakash_steel.prakash_steel.doctype.production_planning.production_planning.get_fg_items_for_production_planning",
		args: { production_planning: frm.doc.production_planning },
		callback(r) {
			const rows = (r && r.message) || [];
			let fg_items = [...new Set(rows.filter(r => r.fg_item).map(r => r.fg_item))];
			let raw_materials = [...new Set(rows.filter(r => r.raw_material).map(r => r.raw_material))];

			frm.set_df_property("finished", "options", "\n" + fg_items.join("\n"));
			frm.set_df_property("material", "options", "\n" + raw_materials.join("\n"));
			frm.refresh_field("finished");
			frm.refresh_field("material");
		}
	});
}

// Auto-calculate stock_available_in_warehouse based on material,
// actual_rm_consumption and rm_source_warehouse
frappe.ui.form.on("Bright Bar Production", {
	material(frm) {
		update_stock_available_in_warehouse(frm);
	},

	actual_rm_consumption(frm) {
		update_stock_available_in_warehouse(frm);
		update_wastage_per(frm);
	},

	rm_source_warehouse(frm) {
		update_stock_available_in_warehouse(frm);
	},

	fg_weight(frm) {
		update_wastage_per(frm);
	},
});

function update_stock_available_in_warehouse(frm) {
	const item_code = frm.doc.material;
	const warehouse = frm.doc.rm_source_warehouse;
	const has_consumption_value =
		frm.doc.actual_rm_consumption !== null &&
		frm.doc.actual_rm_consumption !== undefined &&
		frm.doc.actual_rm_consumption !== "";
	const consumption = flt(frm.doc.actual_rm_consumption) || 0;

	// If any of the required values are missing, clear the field and exit
	if (!item_code || !warehouse || !has_consumption_value) {
		frm.set_value("stock_available_in_warehouse", null);
		return;
	}

	console.log(
		"🔎 Calculating stock_available_in_warehouse for",
		item_code,
		warehouse,
		consumption
	);

	frappe.call({
		method:
			"prakash_steel.api.get_available_stock.get_available_stock_for_warehouse",
		args: {
			item_code: item_code,
			warehouse: warehouse,
		},
		callback(r) {
			const available_qty = (r && r.message) || 0;
			// Remaining stock after this consumption
			const remaining = available_qty - consumption;

			console.log(
				"📊 Stock calculation → available:",
				available_qty,
				"consumption:",
				consumption,
				"remaining:",
				remaining
			);

			// Show remaining stock in stock_available_in_warehouse
			frm.set_value("stock_available_in_warehouse", remaining);

			// Auto-set stock_consumption_status based on remaining value
			if (remaining < 0) {
				frm.set_value("stock_consumption_status", "Stock Exceeded");
			} else if (remaining === 0) {
				frm.set_value("stock_consumption_status", "All Stock");
			} else {
				frm.set_value("stock_consumption_status", "Stock Left");
			}
		},
	});
}

function update_wastage_per(frm) {
	const has_fg_value =
		frm.doc.fg_weight !== null &&
		frm.doc.fg_weight !== undefined &&
		frm.doc.fg_weight !== "";
	const has_rm_value =
		frm.doc.actual_rm_consumption !== null &&
		frm.doc.actual_rm_consumption !== undefined &&
		frm.doc.actual_rm_consumption !== "";

	if (!has_fg_value || !has_rm_value) {
		frm.set_value("wastage_per", null);
		return;
	}

	const fg_weight = flt(frm.doc.fg_weight) || 0;
	const actual_rm = flt(frm.doc.actual_rm_consumption) || 0;

	// Prevent division by zero
	if (actual_rm === 0) {
		frm.set_value("wastage_per", null);
		return;
	}

	// Formula: x = ((fg_weight / actual_rm_consumption) * 100)
	// Then: y = absolute value of (x - 100)
	// wastage_per = y
	const x = (fg_weight / actual_rm) * 100;
	const y = Math.abs(x - 100);
	const wastage = y;

	frm.set_value("wastage_per", wastage);
}
