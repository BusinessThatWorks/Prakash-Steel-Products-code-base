frappe.listview_settings["JOB Work Order"] = {
    get_indicator: function (doc) {
        const indicator_map = {
            Pending: "red",
            "In-Process": "blue",
            "Material Transferred": "pink",
            "Partially Received": "yellow",
            Completed: "green",
        };
        const color = indicator_map[doc.status] || "blue";
        return [doc.status, color, "status,=," + doc.status];
    },
};
