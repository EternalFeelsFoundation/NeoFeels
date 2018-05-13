window.addEventListener('load', function () {
    /* Applies proper color to text denoted as "greentext" */
    var re = /^&gt;(.*)/g;
    var feels = document.querySelectorAll('.post .panel-body');

    for (var i = 0; i < feels.length; i++) {
        var body = feels[i].innerHTML.trimLeft(); // Get textnode value
        var lines = body.split("<br>");
        for (var j = 0; j < lines.length; j++) {
            console.log(lines[j]);
            lines[j] = lines[j].replace(re, "<span class=\"green-text\">&gt;$1</span>");
        }
        var newBody = lines.join("<br>");
        feels[i].innerHTML = newBody;
    }
});

function transformReply() {
    var $post = $(this);
    var $footnote = $post.children('.footnote');
    $post.find('.reply-btn').click(function () {
        var classes = ($footnote.attr('class').split(/\s+/));
        for (var i = 0; i < classes.length; i++) {
            if (classes[i] == 'hide') {
                $footnote.removeClass('hide');
                $footnote.find('textarea').focus();
            }
            else
                $footnote.addClass('hide');
        }

        /* Resize the quick reply textarea when user presses enter */
        $textarea = $footnote.find('textarea');
        $textarea.keypress(function (e) {
            if (e.which == 13) {
                $(this).height($(this).height() + 10 + 'px');
            }
        });
    });
}

function toggleDarkTheme() {
    if (sessionStorage.getItem("dark")) {
        $('#darkTheme').remove();
        sessionStorage.removeItem("dark");
    }
    else {
        sessionStorage.setItem("dark", "true");
        var cssId = 'darkTheme';
        if (!document.getElementById(cssId))
        {
            var head  = document.getElementsByTagName('head')[0];
            var link  = document.createElement('link');
            link.id   = cssId;
            link.rel  = 'stylesheet';
            link.type = 'text/css';
            link.href = 'http://bootswatch.com/darkly/bootstrap.min.css';
            link.media = 'all';
            head.appendChild(link);
        }
    }
}

function toggleDankTheme() {
    if (sessionStorage.getItem("dank")) {
        $('#dankTheme').remove();
        sessionStorage.removeItem("dank");
    }
    else {
        sessionStorage.setItem("dank", "true");
        var cssId = 'dankTheme';
        if (!document.getElementById(cssId))
        {
            var head  = document.getElementsByTagName('head')[0];
            var link  = document.createElement('link');
            link.id   = cssId;
            link.rel  = 'stylesheet';
            link.type = 'text/css';
            link.href = '/static/dank.css';
            link.media = 'all';
            head.appendChild(link);
        }
    }
}



$('.post').each(transformReply);

if (!$('.post-form').hasClass('show')) {
    $('.post-form').toggle();
}
$('#post-btn').click(function () {
    $('.post-form').toggle();
});


if (sessionStorage.getItem("dark")) {
    sessionStorage.removeItem("dark");
    toggleDarkTheme();
}
if (sessionStorage.getItem("dank")) {
    sessionStorage.removeItem("dank");
    toggleDankTheme();
}

$('#darktheme-toggle').click(toggleDarkTheme);
$('#danktheme-toggle').click(toggleDankTheme);

$('#feeltofeel').keyup(updateCount);
$('#feeltofeel').keydown(updateCount);

function updateCount() {
    var cs = $(this).val().length;
    $('#characters').text(cs + "/400");
}

var easter_egg = new Konami(function() { document.getElementById('danktheme-toggle').style.display = 'inline-block';});
