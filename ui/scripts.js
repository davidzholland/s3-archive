const thumb_base_url = 'file:///Users/david/Thumbs/';

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
        });
        return false;
    });
});