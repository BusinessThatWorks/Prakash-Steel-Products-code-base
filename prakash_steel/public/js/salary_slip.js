const BASIC_COMPONENT = "Basic";
const HRA_ABBR = "HRA";
const LOG_PREFIX = "[Salary Slip · Extra Payable]";

function round_extra_payable_amount(value) {
	const amount = flt(value || 0);
	const integer_part = Math.floor(amount);
	const decimal_part = amount - integer_part;

	// Business rule: round up only when decimal is strictly greater than 0.50.
	if (decimal_part > 0.5) {
		return Math.ceil(amount);
	}

	return integer_part;
}

function evaluate_formula_with_abbr(formula, abbr_values) {
	if (!formula) return 0;

	const substituted = formula.replace(/\b[A-Za-z_][A-Za-z0-9_]*\b/g, (token) => {
		const token_lower = token.toLowerCase();
		if (Object.prototype.hasOwnProperty.call(abbr_values, token_lower)) {
			return String(flt(abbr_values[token_lower]));
		}
		return token;
	});

	// Keep formula evaluation restricted to numeric arithmetic expressions.
	if (/[A-Za-z_]/.test(substituted) || /[^0-9+\-*/().%<>=!? :&|]/.test(substituted)) {
		throw new Error(`Unsupported tokens in formula: ${formula}`);
	}

	return flt(Function(`"use strict"; return (${substituted});`)());
}

function set_extra_payable_from_basic(frm) {
	console.log(LOG_PREFIX, "1) Start", {
		extra_payable_days: frm.doc.custom_extra_payable_days,
		start_date: frm.doc.start_date,
		salary_structure: frm.doc.salary_structure,
	});

	const extra_days = frm.doc.custom_extra_payable_days || 0;

	if (!extra_days || !frm.doc.start_date || !frm.doc.salary_structure) {
		console.log(LOG_PREFIX, "2) Stop — missing input", {
			has_extra_days: !!extra_days,
			has_start_date: !!frm.doc.start_date,
			has_salary_structure: !!frm.doc.salary_structure,
		});
		frm.set_value("custom_extra_payable_amount", 0);
		return;
	}

	console.log(LOG_PREFIX, "3) Fetching Salary Structure", frm.doc.salary_structure);

	frappe.db
		.get_doc("Salary Structure", frm.doc.salary_structure)
		.then((struct) => {
			console.log(LOG_PREFIX, "4) Loaded Salary Structure", {
				name: struct.name,
				earnings_rows: (struct.earnings || []).length,
			});

			const earnings = struct.earnings || [];
			const basic_row = earnings.find((row) => row.salary_component === BASIC_COMPONENT);
			const basic_amount = basic_row ? flt(basic_row.amount) : 0;
			const abbr_values = {};

			earnings.forEach((row) => {
				if (row.abbr) {
					abbr_values[row.abbr.toLowerCase()] = flt(row.amount || 0);
				}
			});
			if (basic_row && basic_row.abbr) {
				abbr_values[basic_row.abbr.toLowerCase()] = basic_amount;
			}

			console.log(LOG_PREFIX, "5) Basic row from earnings", {
				looking_for_component: BASIC_COMPONENT,
				found: !!basic_row,
				row: basic_row || null,
				basic_amount,
			});

			if (!basic_amount) {
				console.log(LOG_PREFIX, "6) Stop — Basic amount is 0 or row missing");
				frm.set_value("custom_extra_payable_amount", 0);
				return;
			}

			let hra_amount = 0;
			const hra_row = earnings.find((row) => row.abbr === HRA_ABBR || row.salary_component === "HRA");

			console.log(LOG_PREFIX, "6) HRA row check", {
				looking_for_abbr: HRA_ABBR,
				found: !!hra_row,
				row: hra_row || null,
			});

			if (hra_row) {
				try {
					const direct_hra_amount = flt(hra_row.amount || 0);
					hra_amount = direct_hra_amount;

					if (!hra_amount && hra_row.formula) {
						hra_amount = evaluate_formula_with_abbr(hra_row.formula, abbr_values);
					}

					console.log(LOG_PREFIX, "7) HRA amount resolved", {
						direct_amount: direct_hra_amount,
						formula: hra_row.formula || null,
						hra_amount,
						abbr_values,
					});
				} catch (err) {
					console.warn(LOG_PREFIX, "7) Could not evaluate HRA formula, defaulting HRA to 0", {
						formula: hra_row.formula || null,
						error: err?.message || err,
					});
				}
			}

			const total_monthly_amount = basic_amount + hra_amount;

			const start = frappe.datetime.str_to_obj(frm.doc.start_date);
			const year = start.getFullYear();
			const month = start.getMonth() + 1;
			const total_days_in_month = new Date(year, month, 0).getDate();

			console.log(LOG_PREFIX, "8) Calendar from start_date", {
				start_date_raw: frm.doc.start_date,
				year,
				month,
				total_days_in_month,
			});

			const per_day = total_monthly_amount / total_days_in_month;
			const extra_amount = per_day * extra_days;
			const final_extra_amount = round_extra_payable_amount(extra_amount);

			console.log(LOG_PREFIX, "9) Formula", {
				formula: "((basic_amount + hra_amount) / total_days_in_month) * extra_days",
				basic_amount,
				hra_amount,
				total_monthly_amount,
				total_days_in_month,
				per_day,
				extra_days,
				extra_amount,
				rounding_rule: "decimal > 0.50 => ceil, else floor",
				final_extra_amount,
			});

			frm.set_value("custom_extra_payable_amount", final_extra_amount);
			console.log(LOG_PREFIX, "10) Set custom_extra_payable_amount", final_extra_amount);
		})
		.catch((err) => {
			console.error(LOG_PREFIX, "Error loading Salary Structure", err);
			frm.set_value("custom_extra_payable_amount", 0);
		});
}

frappe.ui.form.on("Salary Slip", {
	custom_extra_payable_days: function (frm) {
		set_extra_payable_from_basic(frm);
	},
	salary_structure: function (frm) {
		set_extra_payable_from_basic(frm);
	},
	start_date: function (frm) {
		set_extra_payable_from_basic(frm);
	},
});
