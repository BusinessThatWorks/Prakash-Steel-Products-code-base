frappe.query_reports["Transporter Bill Payment"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 0,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 0,
		},
		{
			fieldname: "transporter_name",
			label: __("Transporter Name"),
			fieldtype: "Link",
			options: "Supplier",
			reqd: 0,
			get_query: function () {
				return {
					filters: {
						is_transporter: 1,
					},
				};
			},
		},
	],

	onload: function (report) {
		// Frappe sets title / Bootstrap tooltip attributes after render.
		// Strip all tooltip-related attributes with a generous delay.
		function removeTransporterTooltip() {
			var $input = report.page.wrapper
				.find('[data-fieldname="transporter_name"], input[data-fieldname="transporter_name"]');

			$input
				.removeAttr("title")
				.removeAttr("data-original-title")
				.removeAttr("data-bs-original-title")
				.attr("title", "")
				.attr("data-original-title", "")
				.attr("data-bs-original-title", "");

			// Also destroy any Bootstrap tooltip instance attached to it
			try {
				$input.tooltip("dispose");
			} catch (e) { /* ignore if tooltip plugin not active */ }
		}

		// Run at multiple intervals to catch Frappe's late attribute injection
		setTimeout(removeTransporterTooltip, 200);
		setTimeout(removeTransporterTooltip, 600);
		setTimeout(removeTransporterTooltip, 1500);
	},
};

