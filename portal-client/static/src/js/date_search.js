odoo.define('portal-client.date_search', function (require) {
    'use strict';

    console.log('Date search initialized');

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.YourSearchWidget = publicWidget.Widget.extend({
        selector: '.o_searchview button',
        events: {
            'click': '_onClickApply',
        },

        // Handle click on the "Apply" button
        _onClickApply: function (ev) {
            ev.preventDefault();
            // Add your search logic here
            console.log('Apply button clicked');

            // Retrieve the selected dates from the input fields
            var fromDate = $('#date_from').val();
            var toDate = $('#date_to').val();
            console.log(fromDate);
            console.log(toDate);
            // Trigger the search action
            this.do_search(fromDate, toDate);
        },

        // Implement your search logic here
        do_search: function (fromDate, toDate) {
        // Construct the URL with the date_from and date_to parameters
            var url = '/my/client';
            if (fromDate && toDate) {
                url += '?search=True&search_in=from_to' + '&date_begin=' + fromDate + '&date_end=' + toDate;
            }
            window.location.href = url;
        },
    });
});
