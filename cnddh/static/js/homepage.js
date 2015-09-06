$(document)
  .ready(function() {

    var changeSides = function() {
        $('.ui.shape')
          .eq(0)
            .shape('flip over')
            .end()
          .eq(1)
            .shape('flip over')
            .end()
          .eq(2)
            .shape('flip back')
            .end()
          .eq(3)
            .shape('flip back')
            .end()		
        ;
    }; 
	
	$('#acao').click(function() {
	  $('#cform').submit();
	});

    $('.ui.dropdown')
      .dropdown({
        on: 'hover'
      })
    ;

    $('.masthead .information')
      .transition('scale in')
    ;

	$('.message .close').on('click', function() {
		$(this).closest('.message').fadeOut();
	});
	
	setInterval(changeSides, 3000);

  });