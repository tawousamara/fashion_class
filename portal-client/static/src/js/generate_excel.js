odoo.define('portal-client.generate_excel', function (require) {
    "use strict";
    
    console.log("generate excel js loaded");

    var ajax = require('web.ajax');

    $(document).ready(function () {
        $('#generate_excel_button').click(function () {
            // Make an AJAX request to call the Python function
	    ajax.jsonRpc('/my/client/generate_excel', 'call', {})
                .then(function (data) {
                    if (data && data.excel_content) {
                        // Convert the csv content to a Blob
                        var excelData = data.excel_content;
                        var excelBlob = new Blob([excelData], { type: 'text/csv' }); //'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

                        // Create a URL for the Blob
                        var excelUrl = URL.createObjectURL(excelBlob);

                        // Open the PDF in a new tab
                        window.open(excelUrl);
                    } else {
                        // Handle any error or show a message
                        alert('Failed to generate excel');
                    }
                });
        });
    });
});

