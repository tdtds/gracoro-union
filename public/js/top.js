/*
 * top.js: client side script of top page on gracoro union.
 */
$(function(){
	var people = 0, count = 0;
	$('#ranking li span').each(function(){
		people++;
		count += parseInt($(this).text());
	});
	$('#ranking h2').append('&nbsp;<span class="count">' + people + '人で食べたグラコロ、ただいま' + count + '</span>');

	if($('#ranking li.hide').size() > 0){
		$('#ranking').append('<a class="showall" href="">すべて表示</a>');
		$('#ranking a.showall').click(function(){
			$('#ranking li.hide').show();
			$('#ranking a.showall').hide();
			return false;
		});
	}
});
