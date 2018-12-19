$(document).ready(function () {
    $(".btn").mPageScroll2id();
    $(".mapbut").mPageScroll2id();
});

$(window).load(function () {
    $(".loaderInner").fadeOut();
    $(".loader").delay(400).fadeOut("slow");
});

if (ege_data.length !== 0) {
    var marksCanvas = document.getElementById("EGE");
    var chartOptions = {
        scale: {
            ticks: {
                beginAtZero: true,
                min: 0,
                max: 100,
                stepSize: 10
            },
            pointLabels: {
                fontFamily: "Raleway",
                fontSize: 15
            }
        },
        legend: {
            display: false
        }
    };

    var radarChart = new Chart(marksCanvas, {
        type: 'radar',
        data: ege_data,
        options: chartOptions
    });
}

if (oge_data.length !== 0) {
    var canvas = document.getElementById("OGE");

    var options = {
        scale: {
            ticks: {
                beginAtZero: true,
                min: 2,
                max: 5,
                stepSize: 1
            },
            pointLabels: {
                fontFamily: "Raleway",
                fontSize: 15
            }
        },
        legend: {
            display: false
        }
    };
    var radarChartOge = new Chart(canvas, {
        type: 'radar',
        data: oge_data,
        options: options
    });
}

if (vyzes_data.length !== 0) {
    canvas = document.getElementById("VYZES");

    options = {
        responsive: true,
        legend: {
            position: 'bottom',
            title: {
                display: false
            }
        }
    };
    var pieChart = new Chart(canvas, {
        type: 'pie',
        data: vyzes_data,
        options: options
    });
}
