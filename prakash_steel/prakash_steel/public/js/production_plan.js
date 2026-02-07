// Client script for core "Production Plan" DocType
// This script provides console logging for Billet Cutting creation
// The actual creation happens server-side via on_submit hook in hooks.py

frappe.ui.form.on("Production Plan", {
    refresh(frm) {
        // Log when form loads/refreshes
        console.log("🔄 Production Plan form refreshed");
        console.log("📄 Doc name:", frm.doc.name);
        console.log("🧾 Naming Series:", frm.doc.naming_series);
        console.log("📊 DocStatus:", frm.doc.docstatus);
        
        // If document is submitted and has "Rolled Plan" in naming_series,
        // check if Billet Cutting docs were created
        if (frm.doc.docstatus === 1 && frm.doc.naming_series && frm.doc.naming_series.includes("Rolled Plan")) {
            console.log("✅ Production Plan is submitted with 'Rolled Plan' naming series");
            console.log("🔍 Checking for Billet Cutting documents...");
            
            // Query for Billet Cutting docs linked to this Production Plan
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Billet Cutting",
                    filters: {
                        production_plan: frm.doc.name
                    },
                    fields: ["name", "billet_size", "finish_size", "posting_date"]
                },
                callback: function(r) {
                    if (r.message) {
                        console.log(`📋 Found ${r.message.length} Billet Cutting document(s) for this Production Plan:`);
                        r.message.forEach((doc, idx) => {
                            console.log(`  [${idx + 1}] ${doc.name} | billet_size: ${doc.billet_size} | finish_size: ${doc.finish_size} | posting_date: ${doc.posting_date}`);
                        });
                    }
                }
            });
        }
    },
    
    on_submit(frm) {
        // Client-side logging when submit button is clicked
        console.log("=".repeat(60));
        console.log("🚀 Production Plan SUBMIT button clicked (client-side)");
        console.log("📄 Doc name:", frm.doc.name);
        console.log("🧾 Naming Series:", frm.doc.naming_series);
        console.log("=".repeat(60));
        
        const naming_series = (frm.doc.naming_series || "").trim();
        
        if (naming_series && naming_series.includes("Rolled Plan")) {
            console.log("✅ 'Rolled Plan' detected in naming_series");
            console.log("⏳ Server-side hook will create Billet Cutting documents after submit...");
            console.log("📝 Watch server logs and browser console for details");
        } else {
            console.log("⏭️ Not a 'Rolled Plan' - Billet Cutting creation will be skipped");
        }
    },
});



