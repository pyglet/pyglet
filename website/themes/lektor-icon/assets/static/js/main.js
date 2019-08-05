/*
Lektor-Icon Theme
Copyright (c) 2016- Lektor-Icon Contributors

Original standalone HTML5 theme distributed under the terms of the
Creative Commons Attribution 3.0 license -->
https://creativecommons.org/licenses/by/3.0/

Additions, modifications and porting released under the terms of the
MIT (Expat) License: https://opensource.org/licenses/MIT
See the LICENSE.txt file for more details
https://github.com/spyder-ide/lektor-icon/blob/master/LICENSE.txt

For information on the included third-party assets, see NOTICE.txt
https://github.com/spyder-ide/lektor-icon/blob/master/NOTICE.txt
*/


;(function () {

    'use strict';


    // Fullsize Error Page Background
    var fullHeight = function() {
        $('#error-page').css('height', $(window).height() - $('.js-sticky').height() - $('#fh5co-footer').outerHeight());
    };

    var setFullHeight = function() {
        fullHeight();
        $(window).on('resize', fullHeight);
    };


    // Offcanvas layout for "hamburger" mobile menu
    var offcanvasMenu = function() {
        $('body').prepend('<div id="fh5co-offcanvas"></div>');
        $('body').prepend('<a href="#" class="js-fh5co-nav-toggle fh5co-nav-toggle" aria-label="Toggle for hamburger menu"><i></i></a>');

        $('.fh5co-main-nav .fh5co-menu-1 a, .fh5co-main-nav .fh5co-menu-2 a').each(function(){

            var $this = $(this);

            $('#fh5co-offcanvas').append($this.clone());
        });
        // $('#fh5co-offcanvas').append
    };


    // Top navbar stickiness
    var mainMenuSticky = function() {

        var sticky = $('.js-sticky');
        var $section = $('.fh5co-main-nav');

        sticky.css('height', sticky.height());
        $(window).on('resize', function(){
            sticky.css('height',  $section.height());
        });

        $section.waypoint(function(direction) {

            if (direction === 'down') {

                    $section.css({
                        'position' : 'fixed',
                        'top' : 0,
                        'width' : '100%',
                        'z-index' : 99999
                    }).addClass('fh5co-shadow');;
            }
        }, {
            offset: '0px'
        });
    };


    // Mobile "burger" menu
    var burgerMenu = function() {

        $('body').on('click', '.js-fh5co-nav-toggle', function(event){

            var $this = $(this);

            if( $('body').hasClass('offcanvas-visible') ) {
                $('body').removeClass('offcanvas-visible fh5co-overflow');
                $this.removeClass('active');
            } else {
                $('body').addClass('offcanvas-visible fh5co-overflow');
                $this.addClass('active');
            }
            event.preventDefault();
        });
    };


    // Click outside of offcanvas sidebar to close it
    var mobileMenuOutsideClick = function() {

        $(document).on('click', function (e) {
        var container = $("#fh5co-offcanvas, .js-fh5co-nav-toggle");
        if (!container.is(e.target) && container.has(e.target).length === 0) {

            if ( $('body').hasClass('offcanvas-visible') ) {

                $('body').removeClass('offcanvas-visible');
                $('.js-fh5co-nav-toggle').removeClass('active');
            }
        }
        });
    };



    // Document on load
    $(function(){
        offcanvasMenu();
        mainMenuSticky();
        setFullHeight();
        burgerMenu();
        mobileMenuOutsideClick();
    });

}());
