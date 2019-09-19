const thumb_base_url = '';

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
$(function () {
    $("#search").submit(function(event) {
        $("#items").empty();
        var post_url = $(this).attr("action"); //get form action url
        var request_method = $(this).attr("method"); //get form GET/POST method
        var form_data = $(this).serialize(); //Encode form elements for submission
        $.ajax({
            url : post_url,
            type: request_method,
            data : JSON.stringify(form_data),
            dataType: 'json'
        }).done(function(response) {
            $(response.Items).each(function(idx, obj) {
                var html = '<div class="item">';
                    html += '<img alt="' + getImgAltText(obj) + '" src="' + thumb_base_url + obj.Name + '" height="200" width="300" />';
                    html += '</div>';
                $("#items").append(html);
            });
        });
        return false;
    });
});