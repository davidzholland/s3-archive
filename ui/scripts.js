const thumb_base_url = 'file:///Users/david/Thumbs/';
const orig_base_url = '/Volumes/Public/Shared Pictures/';
let currentPage = 1;
let total = 0;
let count = 0;
const itemsPerPage = 100;

function getImgAttribute(img, name) {
    $(img.Attributes).each(function(idx, obj) {
        if (obj.Name == name) {
            return obj.Name;
        }
    });
    return '';
}
function getImgAltText(img) {
    var headline = getImgAttribute(img, 'headline');
    if (headline != '') return headline;
    var caption = getImgAttribute(img, 'caption');
    if (caption != '') return caption;
    return img.Name;
}

function search(page) {
    updatePaginationButtons();
    updatePaginationCounts(true);
    $("#next").attr('disabled', 'disabled');
    $("#results").addClass('loading');
    $("#search [name='page']").val(page);
    var post_url = $("#search").attr("action"); //get form action url
    var request_method = $("#search").attr("method"); //get form GET/POST method
    var form_data = $("#search").serialize(); //Encode form elements for submission
    $.ajax({
        url : post_url,
        type: request_method,
        data : JSON.stringify(form_data),
        dataType: 'json'
    }).done(function(response) {
        $("#items").empty();
        total = response.total;
        if (typeof response.count != 'undefined') {
            count = response.count;
        }
        $(response.results.Items).each(function(idx, obj) {
            var thumb_path = thumb_base_url + obj.Name;
            var orig_path = orig_base_url + obj.Name;
            if (obj.Name.toLowerCase().substr(-4) != '.jpg') {
                thumb_path += '.jpg';
            }
            var placeholder_path = 'https://image.flaticon.com/icons/png/512/23/23765.png';
            if (obj.Name.toLowerCase().substr(-4) == '.jpg' || obj.Name.toLowerCase().substr(-5) == '.jpeg') {
                placeholder_path = 'https://image.flaticon.com/icons/png/512/29/29264.png';
            } else if (obj.Name.toLowerCase().substr(-4) == '.zip') {
                placeholder_path = 'https://image.flaticon.com/icons/svg/28/28814.svg';
            }
            var html = '<div class="item">';
                html += '<div class="thumb">';
                html += '<span class="helper"></span>';
                html += '<object data="' + thumb_path + '" type="image/jpg" alt="' + getImgAltText(obj) + '" title="' + getImgAltText(obj) + '">';
                html += '<img src="' + placeholder_path + '" height="50" />';
                html += '</object>';
                html += '</div>';
                html += '<div class="caption"><ul>';
                html += '<li>original: ' + orig_path + '</li>';
                for (const attribute of obj.Attributes) {
                    if (attribute.Value != '') {
                        html += '<li>' + attribute.Name + ': ' + attribute.Value + '</li>';
                    }
                }
                html += '</ul></div>';
                html += '</div>';
            $("#items").append(html);
        });
        updatePaginationButtons();
        updatePaginationCounts();
        if ($("#results").scrollTop() == 0) {
            $("#results").removeClass('loading');
        } else {
            $("#results").animate({ scrollTop: 0 }, "slow", function() {
                $("#results").removeClass('loading');
            });
        }
    });
}

function updatePaginationButtons() {
    if (currentPage == 1) {
        $("#prev").attr('disabled', 'disabled');
    } else {
        $("#prev").removeAttr('disabled');
    }
    if (currentPage >= Math.ceil(count / itemsPerPage)) {
        $("#next").attr('disabled', 'disabled');
    } else {
        $("#next").removeAttr('disabled');
    }
}

function updatePaginationCounts(loading = false) {
    const start = ((currentPage - 1) * itemsPerPage) + 1;
    let end = (start - 1) + $("#results .item").length;
    if (end > count) {
        end = count;
    }
    let countText = 'No matched results';
    if (loading) {
        countText = 'Loading...';
    }
    if (end > 0) {
        countText = numberWithCommas(start) + '-' + numberWithCommas(end) + ' of ' + numberWithCommas(count);
    }
    if (total > count) {
        countText += ' (total: ' + numberWithCommas(total) + ')';
    }
    $("#count").text(countText);
    // Pages links
    let pagesHTML = '<ul>';
    const pages = Math.ceil(count / itemsPerPage);
    const pagesToDisplay = 10;
    let startPage = currentPage - Math.floor(pagesToDisplay / 2);
    if (startPage < 1) {
        startPage = 1;
    }
    let endPage = startPage + pagesToDisplay;
    if (endPage > pages) {
        endPage = pages;
    }
    for (let page = startPage; page <= endPage; page++) {
        if (page == currentPage) {
            pageHTML = '<b>' + page + '</b>';
        } else {
            pageHTML = '<a href="" data-page="' + page + '">' + page + '</a>';
        }
        pagesHTML += '<li>' + pageHTML + '</li>';
    }
    pagesHTML += '</ul>';
    $(".pages").html(pagesHTML);
    $(".pages a").click(function() {
        currentPage = Number($(this).attr('data-page'));
        search(currentPage);
        return false;
    });
}

function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

$(function () {
    $("#prev").click(function(event) {
        currentPage--;
        if (currentPage < 0) currentPage = 0;
        search(currentPage);
    });
    $("#next").click(function(event) {
        currentPage++;
        search(currentPage);
    });
    $("#search").submit(function(event) {
        currentPage = 1;
        search(1);
        return false;
    });
    search(1);
});
