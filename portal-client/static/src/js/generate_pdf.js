odoo.define('portal-client.generate_pdf', function (require) {
    "use strict";
    
    console.log("generate pdf js loaded");

    var ajax = require('web.ajax');

    $(document).ready(function () {
        $('#generate_pdf_button').click(function () {
            // Make an AJAX request to call the Python function
	    ajax.jsonRpc('/my/client/generate_pdf', 'call', {})
                .then(function (data) {
                    if (data && data.pdf_content) {
                        // Convert the PDF content to a Blob
                        var pdfData = atob(data.pdf_content);
                        var pdfBlob = new Blob([pdfData], { type: 'application/pdf' });

                        // Create a URL for the Blob
                        var pdfUrl = URL.createObjectURL(pdfBlob);

                        // Open the PDF in a new tab
                        var w = window.open(pdfUrl);
                    } else {
                        // Handle any error or show a message
                        alert('Failed to generate PDF.');
                    }
                });
        });
    });
});

