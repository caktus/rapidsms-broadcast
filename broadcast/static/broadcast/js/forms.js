/* forms.js
 * General, shared javascript form functionality
 */
$(document).ready(function() {
    $("form.buttons input[name=submit], form.buttons input[name=cancel]").button();
    $("form.buttons input[name=cancel]").click(function(e) {
        history.go(-1);
    });
});

