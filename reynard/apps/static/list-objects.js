$(document).ready(function (e) {
    $("#action").change(function (e) {
        if ( ($(this).val() != '') && ($(this).val() != '-- Choose --') ) {
            
            if ( ($(this).val() == 'del') &&
                 confirm("Are you sure you want to delete?") )
            {
                $('#list-object-form').trigger('submit');
            }

        }
    });

    $(".delete-obj").click(function (e) {
        var id;

        if (confirm("Are you sure you want to delete this object?")) {
            
            id = this.id.split('-')[2];

            $(".select").each(function (e) {
                this.checked = '';
            });
            
            document.getElementById("select_" + id).checked = 'checked';
            document.getElementById("action").value = 'del';
            $("#list-object-form").trigger('submit');
        }

        e.preventDefault();
    });

});
