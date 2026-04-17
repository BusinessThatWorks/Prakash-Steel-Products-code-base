frappe.query_reports["Day Book Entries"] = {
	filters: [
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "party_name",
			label: __("Party Name"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.xcall("prakash_steel.prakash_steel.report.day_book_entries.day_book_entries.get_filter_options", {
					fieldname: "party_name",
					txt: txt || "",
					date: frappe.query_report.get_filter_value("date"),
				});
			},
		},
		{
			fieldname: "vch_type",
			label: __("Vch Type"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.xcall("prakash_steel.prakash_steel.report.day_book_entries.day_book_entries.get_filter_options", {
					fieldname: "vch_type",
					txt: txt || "",
					date: frappe.query_report.get_filter_value("date"),
				});
			},
		},
		{
			fieldname: "vch_no",
			label: __("Vch No."),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.xcall("prakash_steel.prakash_steel.report.day_book_entries.day_book_entries.get_filter_options", {
					fieldname: "vch_no",
					txt: txt || "",
					date: frappe.query_report.get_filter_value("date"),
				});
			},
		},
	],
};
