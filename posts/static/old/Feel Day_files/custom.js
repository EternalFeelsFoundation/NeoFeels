




/*
     FILE ARCHIVED ON 14:48:20 Mar 23, 2014 AND RETRIEVED FROM THE
     INTERNET ARCHIVE ON 0:51:22 Nov 6, 2015.
     JAVASCRIPT APPENDED BY WAYBACK MACHINE, COPYRIGHT INTERNET ARCHIVE.

     ALL OTHER CONTENT MAY ALSO BE PROTECTED BY COPYRIGHT (17 U.S.C.
     SECTION 108(a)(3)).
*/
window.addEventListener('load',function(){var re=/(\&gt;.*)/gm;var feels=document.querySelectorAll('.feel');for(var i=0;i<feels.length;i++){var body=feels[i].innerHTML.trimLeft();var newBody=body.replace(re,"<span class=\"green-text\">$1</span>");console.log(newBody);feels[i].innerHTML=newBody;}
var timeTags=document.querySelectorAll('.time');for(var i=0;i<timeTags.length;i++){var time=timeTags[i].innerHTML;var date=new Date(time*1000);timeTags[i].innerHTML=date.toLocaleString();}});