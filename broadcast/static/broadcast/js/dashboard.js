google.load('visualization', '1', {'packages':['annotatedtimeline']});
google.setOnLoadCallback(getChartData);
function drawChart(response) {
    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Date');
    data.addColumn('number', 'Incoming Messages');
    data.addColumn('number', 'Outgoing Messages');
    var rows =[];
    $.each(response, function(i, r) {
        rows.push([new Date(r[0]), r[1], r[2]]);
    });
    data.addRows(rows);
    var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('usage-chart'));
    chart.draw(data, {displayAnnotations: false});
}
function getChartData() {
    var url = $('#usage-chart').data('url');
    var now = new Date().getTime();
    $.getJSON(url, {timestamp: now}, drawChart);
}
$(document).ready(function() {
    $('.form-action input[type=submit]').button();
});
