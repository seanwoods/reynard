$(document).ready(function (e) {

    $("#add-field").click(function (e) {
        var opt;
        var val_to_select;
        
        opt = $("#fields-from option:selected");

        if (opt.next().length > 0) {
            val_to_select = opt.next()[0].value;
        } else if (opt.prev().length > 0) {
            val_to_select = opt.prev()[0].value;
        }
        
        opt.detach();
        opt.appendTo("#fields-to");
        
        $("#fields-from").val(val_to_select).focus();
    });
    
    $("#rm-field").click(function (e) {
        var opt;
        var val_to_select;
        
        opt = $("#fields-to option:selected");

        if (opt.next().length > 0) {
            val_to_select = opt.next()[0].value;
        } else if (opt.prev().length > 0) {
            val_to_select = opt.prev()[0].value;
        }
        
        opt.detach();
        opt.appendTo("#fields-from");
        
        $("#fields-to").val(val_to_select).focus();
    });

    $("#move-up").click(function (e) {
        var opt;
        var prev;
        var val;
        
        opt = $("#fields-to option:selected")
        prev = opt.prev()
        val = opt[0].value;
        
        if (prev.length > 0) {
            opt.detach();
            prev.before(opt);
        }

        $("#fields-to").val(val).focus();
    });

    $("#move-down").click(function (e) {
        var opt;
        var prev;

        opt = $("#fields-to option:selected")
        next = opt.next()
        val = opt[0].value;

        if (next.length > 0) {
            opt.detach();
            next.after(opt);
        }

        $("#fields-to").val(val).focus();
    });

    $(".crit-add").live('click', function (e) {
        var row;
        var lastRow;
        
        lastRow = $(this).parent().parent().siblings(".crit-row").last();
        row = lastRow.clone();

        row.children().children().each(function () {
            id = this.id.split('-');
            id[id.length - 1] = parseInt(id[id.length - 1]) + 1;
            
            this.id = id.join('-');
            this.name = id.join('-');
            $(this).val('');
        });

        row.insertAfter(lastRow);
    });

    $(".sort-add").live('click', function (e) {
        var row;
        var lastRow;
        
        lastRow = $(this).parent().parent().siblings(".sort-row").last(); 
        row = lastRow.clone();

        row.children().children().each(function () {
            
            if (this.tagName == 'LABEL') {
                for_ = $(this).attr('for').split('-')
                for_[for_.length - 1] = parseInt(for_[for_.length - 1]) + 1;
                
                $(this).attr('for', for_.join('-'));
            } else {
                id = this.id.split('-');
                nm = this.name.split('-');
                id[id.length - 1] = parseInt(id[id.length - 1]) + 1;
                nm[nm.length - 1] = parseInt(nm[nm.length - 1]) + 1;

                this.id = id.join('-');
                this.name = nm.join('-');
            }
        });
        
        row.insertAfter(lastRow);
    });

    $(".arg-add").live('click', function (e) {
        var row;
        var lastRow;

        lastRow = $(this).parent().parent().siblings(".arg-row").last();
        row = lastRow.clone();

        row.children().children().each(function () {
            id = this.id.split('-');
            id[id.length - 1] = parseInt(id[id.length - 1]) + 1;

            this.id = id.join('-');
            this.name = id.join('-');
            $(this).val('');
        });

        row.insertAfter(lastRow);
    });

    $("#submit").click(function (e) {
        $("#fields-to").children("option").each(function (e) {
            this.selected = true;
        });
    });

});
