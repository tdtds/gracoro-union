/*
 * top.js: client side script of top page on gracoro union.
 */
$(function(){
	if($('#ranking li.hide').size() > 0){
		$('#ranking').append('<a class="showall" href="">すべて表示</a>');
		$('#ranking a.showall').click(function(){
			$('#ranking li.hide').show();
			$('#ranking a.showall').hide();
			return false;
		});
	}
});
