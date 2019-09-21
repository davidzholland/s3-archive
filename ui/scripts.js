const thumb_base_url = 'file:///Users/david/Thumbs/';
let pageTokens = {};
let currentPage = 1;
let total = 0;
let count = 0;
const itemsPerPage = 25;

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
    updatePagination();
    $("#next").attr('disabled', 'disabled');
    $("#items").empty();
    $("#search [name='nextToken']").val(pageTokens[page]);
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
            pageTokens[page + 1] = response.results.NextToken;
            var thumb_path = thumb_base_url + obj.Name;
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
                html += '<span class="helper"></span>';
                html += '<object data="' + thumb_path + '" type="image/jpg" alt="' + getImgAltText(obj) + '" title="' + getImgAltText(obj) + '">';
                html += '<img src="' + placeholder_path + '" height="50" />';
                html += '</object>';
                html += '</div>';
            $("#items").append(html);
        });
        updatePagination();
    });
}

function updatePagination() {
    if (currentPage == 1) {
        $("#prev").attr('disabled', 'disabled');
    } else {
        $("#prev").removeAttr('disabled');
    }
    if (currentPage >= total) {
        $("#next").attr('disabled', 'disabled');
    } else {
        $("#next").removeAttr('disabled');
    }
    const start = ((currentPage - 1) * itemsPerPage) + 1;
    const end = (start - 1) + $("#results .item").length;
    let countText = start + '-' + end + ' of ' + count + ' (total: ' + total + ')';
    $("#count").text(countText);
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
        pageTokens = {};
        currentPage = 1;
        search(1);
        return false;
    });
});
