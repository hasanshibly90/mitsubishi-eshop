(function($) {
    // Initialize a single row
    function initRow($row) {
        console.log("Initializing row:", $row);
        var $productSelect = $row.find('select.product-select');
        var $priceInput = $row.find('input[name$="-unit_price"]');

        console.log("Product select found:", $productSelect.length, "Unit price input found:", $priceInput.length);

        if ($productSelect.length && $priceInput.length) {
            // Unbind old events to avoid duplicates
            $productSelect.off("change").on("change", function() {
                var $selected = $(this).find("option:selected");
                var price = $selected.data("price");
                console.log("Product changed. Selected price:", price);
                if (price !== undefined) {
                    $priceInput.val(price);
                }
            });
        } else {
            console.log("Could not find product select or unit price input in row:", $row);
        }
    }

    // Initialize all existing rows on the page
    function initAllRows() {
        // We look for any element that contains <select class="product-select">
        // This catches both existing rows and new ones
        $('tr, div').filter(function() {
            return $(this).find('select.product-select').length > 0;
        }).each(function() {
            initRow($(this));
        });
    }

    $(document).ready(function() {
        // 1) Initialize all rows on page load
        initAllRows();

        // 2) Use MutationObserver to watch for newly added elements
        //    anywhere inside the main admin form container (#content-main or .inline-group).
        var target = document.querySelector('#content-main form') || 
                     document.querySelector('.inline-group') || 
                     document.body; // fallback if #content-main isn't found

        if (target) {
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    // For each newly added node, check if it contains a product-select
                    if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                        $(mutation.addedNodes).each(function() {
                            if (this.nodeType === 1) { // ELEMENT_NODE
                                var $node = $(this);
                                // If this node or any of its children has a product-select
                                if ($node.is('select.product-select') ||
                                    $node.find('select.product-select').length > 0) {
                                    console.log("New node with product-select detected:", $node);
                                    // Re-init everything, or just initRow($node)
                                    initAllRows();
                                }
                            }
                        });
                    }
                });
            });
            // Observe changes in the subtree for newly added elements
            observer.observe(target, { childList: true, subtree: true });
        } else {
            console.log("No suitable container found for MutationObserver. Will only init once.");
        }
    });
})(django.jQuery);
