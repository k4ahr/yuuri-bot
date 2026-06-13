;(function($) {
	"use strict";
	
	/**
	 * [isMobile description]
	 * @type {Object}
	 */
	window.isMobile = {
		Android: function() {
			return navigator.userAgent.match(/Android/i);
		},
		BlackBerry: function() {
			return navigator.userAgent.match(/BlackBerry/i);
		},
		iOS: function() {
			return navigator.userAgent.match(/iPhone|iPad|iPod/i);
		},
        iPad: function() {
            return navigator.userAgent.match(/iPad/i);
        },
		Opera: function() {
			return navigator.userAgent.match(/Opera Mini/i);
		},
		Windows: function() {
			return navigator.userAgent.match(/IEMobile/i);
		},
		any: function() {
			return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
		}
	}
	window.isIE = /(MSIE|Trident\/|Edge\/)/i.test(navigator.userAgent);
	window.windowHeight = window.innerHeight;
	window.windowWidth = window.innerWidth;

	
	// Returns a function, that, as long as it continues to be invoked, will not
    // be triggered. The function will be called after it stops being called for
    // N milliseconds. If `immediate` is passed, trigger the function on the
    // leading edge, instead of the trailing.
    function debounce(func, wait, immediate) {
        var timeout;
        return function() {
            var context = this, args = arguments;
            var later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            var callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    };

    $.fn.numberTextLine = function(opts) {
        $(this).each( function () {
            var el = $(this),
                defaults = {
                    numberLine: 0
                },
                data = el.data(),
                dataTemp = $.extend(defaults, opts),
                options = $.extend(dataTemp, data);

            if (!options.numberLine)
                return false;

            // el.ellipsis({
            //     lines: 2
            // });

            el.bind('customResize', function(event) {
                event.stopPropagation();
                reInit();
            }).trigger('customResize');
            $(window).resize( function () {
                el.trigger('customResize');
            })
            function reInit() {
                var fontSize = parseInt(el.css('font-size')),
                    lineHeight = parseInt(el.css('line-height')),
                    overflow = fontSize * (lineHeight / fontSize) * options.numberLine;

                el.css({
                    'display': 'block',
                    'display': '-webkit-box',
                    'height': overflow,
                    '-webkit-line-clamp': String(options.numberLine),
                    '-webkit-box-orient': 'vertical',
                    'overflow': 'hidden',
                    'text-overflow': 'ellipsis'
                });
            }
        })
    }

    function wowJs() {
        var wow = new WOW({
            boxClass:     'wow',      // animated element css class (default is wow)
            animateClass: 'animated', // animation css class (default is animated)
            mobile:       true,       // trigger animations on mobile devices (default is true)
            live:         true,       // act on asynchronously loaded content (default is true)
            callback:     function(box) {
                $(box).addClass('effect');
                $(box).removeClass('fix');
            },
            scrollContainer: null // optional scroll container selector, otherwise use window
        });
        wow.init();
    }

    function headerJs() {
        var header = $('.header');
        
        if(header.length) {
            var headeroom = new Headroom(document.querySelector("header"), {
                tolerance : 4,
                offset : 100,
                classes: {
                    pinned: "header-pin",
                    unpinned: "header-unpin"
                },
            });
            headeroom.init();
        }

        const targetBody = document.querySelector('.header__search .item');

        $('.header__iconSearch').on('click', function(e) {
            e.preventDefault();
            header.addClass('show-search');
            $('.header__search .form-control').focus();
            bodyScrollLock.disableBodyScroll(targetBody);
        });

        $('.header__search .item__close').on('click', function(e) {
            e.preventDefault();
            header.removeClass('show-search');
            bodyScrollLock.enableBodyScroll(targetBody);
        });

        $(window).on('load', function() {
            var inner = $('.header__pricePetrol .f-list');
            if( inner.length) {
                setTimeout(function() {
                    var offsetLeft =  Math.floor( $(window).width() - (inner.offset().left+ inner.outerWidth() ) );
                    inner.css('right', offsetLeft*-1);
                }, 100);
            }
        })

    }

    function menuMobileJs() {
        var ww = $(window).width();
        if(ww < 1200) {
            var wrap = $('.menu-mobile__nav'),
                child = $('.menu-has-children', wrap);

            child.each(function() {
                var self = $(this),
                    sub = self.children('.submenu'),
                    getBack = sub.attr('data-en') ? sub.attr('data-en') : 'Quay lại';
                
                if(sub.find('.back').length < 1) {
                    sub.append('<li><span class="back-btn"><i class="fa fa-angle-left"></i>'+getBack+'</span></li>')
                }
            });
        }

        const targetBody = document.querySelector('.menu-mobile__nav');

        $('.header__iconmenu').on('click', function(e) {
            if( $('.menu-mobile').hasClass('menu-mobile--active') ) {
                bodyScrollLock.enableBodyScroll(targetBody);
            }else {
                bodyScrollLock.disableBodyScroll(targetBody);
            }

            $('.header').toggleClass('header-show-mobile');
            $('.menu-mobile').toggleClass('menu-mobile--active'); 
        });

        $('.menu-mobile__pricePetrol .f-btn').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).parent().toggleClass('active');
        });

        $('.menu-mobile__pricePetrol .f-bg').on('click', function(e) {
            $('.menu-mobile__pricePetrol .f-btn').trigger('click');
            
        });

        $('.menu-mobile__nav .menu-has-children').on('click', '> span', function() {
            $(this).next().addClass('show-submenu');
        });

        $(document).on('click', '.menu-mobile__nav .back-btn', function() {
            $(this).closest('.submenu').removeClass('show-submenu');
        });
    }

    function heroSlide() {
        var slidea = $('.hero__bg.owl-carousel');
        var list = $('.hero__list');
        var autoPlay = 9000;

        if( slidea.find('[data-youtube]').length > 0 ) {
            slidea.closest('.hero') .addClass('fix-video');
        }

        slidea.owlCarousel({
            loop: true,
            items : 1,
            dots: false,
            nav : false,
            smartSpeed: 1500,
            pullDrag: false,
        })

        var _setInterval;

        function fix() {
            if( slidea.find('[data-youtube]').length < 1 ) {
                _setInterval = setInterval(function(){
                    slidea.trigger('next.owl.carousel');
                },autoPlay);
            }
        }
        fix();

        slidea.on('changed.owl.carousel', function(e) {
            clearInterval(_setInterval);
            setTimeout(function() {
                var indexs = $(e.currentTarget).find('.owl-item.active .item').attr('data-index');

                list.find('li').removeClass('active');
                list.find('li').eq(indexs).addClass('active');
            }, 100);
            fix();
        });

        list.find('li').on('click', function() {
            clearInterval(_setInterval);
            var self = $(this),
                _index = self.attr('data-index');
            slidea.trigger("to.owl.carousel", [_index]);
        });
    }

    function btnShowMemberJs() {
        const targetBody = document.querySelector('.member-connection__inner');

        $('.btn-show-member').on('click', function(e) {
            e.preventDefault();
            $('.member-connection').addClass('show-content');
            bodyScrollLock.disableBodyScroll(targetBody);
        });

        $('.member-connection .btn-close').on('click', function() {
            $('.member-connection').removeClass('show-content');
            bodyScrollLock.enableBodyScroll(targetBody);
        });
    }

    function selectLanguageJs() {
        $('.select-language').each(function() {
            var self = $(this),
                title = self.find('.f-title span'),
                content = self.find('.f-content');
            
            title.on('click', function(e) {
                e.stopPropagation();
                $(this).parent().toggleClass('active');
            });
            
            $(document).not(content).on('click', function(e) {
                if( title.parent().hasClass('active')) {
                    title.trigger('click')
                }
            })
        });
    }

    function copyToClipboard() {
        $('.btn-share-js').each(function() {
            $(this).on('click', function(e) {
                e.preventDefault();
                var self = $(this);
                var getUrl = window.location.href;
                var getAlert = self.attr('data-alert');              

                var $temp = $("<input>");
                self.after($temp);
                $temp.val(getUrl).select();
                document.execCommand("copy");
                $temp.remove();
                alert(getAlert);
            });
        });
    }

    function historyJs() {
        if($('.sec-history').length) {
            var owlA = $('.sec-history .f-history__slide');
            var owlB = $('.sec-history .f-history__footer .owl-carousel');

            function current(a, b) {
                var getIndex = $(a).find('.owl-item.active .item').attr('data-index');
                b.find('.owl-item').removeClass('current');
                b.find('.owl-item').eq(getIndex).addClass('current');      
                b.trigger("to.owl.carousel", [getIndex]);
            }
            var dataAutoPlay = 2000;

            owlA
                .owlCarousel({
                    items: 1,
                    margin: 30,
                    dots: false,
                    loop: true,
                    navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>'],
                    navContainer: $('.sec-history').find('.nav-slide-custom')[0],
                    smartSpeed: 1000,
                    autoplay:true,
                    autoplayTimeout: dataAutoPlay,
                    autoplayHoverPause:true,
                })
            
            owlB
                .owlCarousel({
                    items: 2,
                    margin: 0,
                    dots: false,
                    nav: false,
                    mouseDrag: false,
                    touchDrag: false,
                    pullDrag: false,
                    freeDrag: false,
                    responsive : {
                        768 : {
                            items: 4,
                        },
                        991 :{
                            items: 5,
                        },
                        1200 : {
                            items: 6,
                            margin: 10,
                        }
                    },
                    onInitialized: function(e) {
                        var getIndex = owlA.find('.owl-item.active .item').attr('data-index');
                        $(e.currentTarget).find('.owl-item').eq(getIndex).addClass('current')
                    }
                })
            
            var fixSetimeout;
            owlA
                .on('changed.owl.carousel', function(e) {
                    setTimeout(function() {
                        current(owlA, owlB)
                    }, 100);
                })
                .on('translate.owl.carousel', function() {
                    owlA.trigger('stop.owl.autoplay');
                    clearTimeout(fixSetimeout);
                })
                .on('translated.owl.carousel', function() {
                    var fixSetimeout = setTimeout(function() {
                        owlA.trigger('play.owl.autoplay',[dataAutoPlay])
                    }, 2000);
                })
            
            owlB.find('.f-date').on('click', function() {
                var getIndex = $(this).attr('data-index');
                owlA.trigger("to.owl.carousel", [getIndex, 300]);
            });
        }
    }

    function ctaTextboxJs() {
        var wrap = $('.cta-textbox__inner .owl-carousel');
        if(wrap.length) {
            wrap.owlCarousel({
                items: 1,
                margin: 0,
                dots: false,
                loop: true,
                smartSpeed: 1000,
                autoplay: true,
                autoplayTimeout: 5000,
                autoplayHoverPause:true,
                responsive : {
                    768: {
                        items: 2
                    },
                }
            })
        }
    }

    function businessResultsJs() {
        var wrap = $('.business-results .owl-carousel');
        if(wrap.length) {
            wrap.owlCarousel({
                items: 6,
                margin: 30,
                nav: true,
                navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>'],
                loop: true,
                smartSpeed: 1000,
                autoplay: true,
                autoplayTimeout: 5000,
                autoplayHoverPause:true,
                responsive : {
                    320: {
                        items: 2,
                        margin: 15,
                    },
                    768: {
                        items: 5,
                        margin: 20,
                    },
                    991: {
                        items: 6,
                    },
                    1200: {
                        margin: 30,
                    }
                }
            })
        }
    }

    function upcomingEventSlideJs() {
        var wrap = $('.upcoming-event .owl-carousel');
        if(wrap.length) {
            wrap.owlCarousel({
                items: 3,
                margin: 50,
                nav: true,
                navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>'],
                loop: true,
                smartSpeed: 1000,
                autoplay: true,
                autoplayTimeout: 5000,
                autoplayHoverPause:true,
                responsive : {
                    320: {
                        items: 1,
                        margin: 15,
                    },
                    768: {
                        items: 2,
                        margin: 30,
                    },
                    991: {
                        margin: 30,
                    },
                }
            })
        }
    }

    function collapseBoxJs() {
        if($('.collapseBox').length) {
            $('.collapseBox').each(function() {
                var self = $(this),
                    content = self.find('.collapseBox__content'),
                    btn = self.find('.collapseBox__btn');

                btn.find('a').on('click', function(e) {
                    e.preventDefault();
                    var _this = $(this);
    
                    if( _this.hasClass('btn-down') ) {
                        self.addClass('show-content');
                        content.slideDown();
                    }else {
                        self.removeClass('show-content');
                        content.slideUp();
                    }
                });
            });
        }
    }

    function tabJs() {
        $('.tabJs').each(function() {
            var self = $(this),
                navList = self.find('.tabJs-nav'),
                contentList = self.find('.tabJs-content');
            
            navList.find('li').on('click', function() {
                var el = $(this),
                    nav2 = el.closest('.tabJs-nav'),
                    content2 = nav2.next();

                if(!el.hasClass('current')) {
                    var getId = el.attr('rel');
                    nav2.find('> li').removeClass('current');
                    content2.find('> .tab-panel').removeClass('current');
                    
                    el.addClass('current');
                    content2.find('#'+getId).addClass('current');
                }
            })
        });
    }

    function popupJs() {
        var magnificPopupDefault = {
            type: 'image',
            overflowY: 'scroll',
            fixedContentPos: true,
            image: {
                markup: `<div class="mfp-figure">
                            <div class="mfp-close"><svg x="0px" y="0px" width="39px" height="38px" viewBox="0 0 39 38"><path id="Line-6" fill="none" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="square" d="M1.738,1.425l35.355,35.354"/><path id="Line-7" fill="none" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="square" d="M1.031,36.779L36.387,1.425"/></svg></div>
                            <div class="mfp-image">
                                <div class="mfp-img"></div>
                            </div>
                            <div class="mfp-bottom-bar">
                                <div class="mfp-title"></div>
                            </div>
                        </div>`,
                tError: '<a href="%url%">The image #%curr%</a> could not be loaded.',
                tCounter: false,
                titleSrc: function(item) {
                    return item.el.attr('title');
                }
            },
            removalDelay: 500,
            showCloseBtn: true,
            closeOnContentClick: false,
            closeBtnInside: true,
            callbacks: {
                beforeOpen: function() {
                    this.st.mainClass = this.st.el.attr('data-effect') ? this.st.el.attr('data-effect') : 'mfp-zoom-in';
                    $('body').addClass('body-fix-scroll');
                },

                close: function() {
                    $('body').removeClass('body-fix-scroll');
                }
            },
            midClick: true
        }

        $('[data-init="magnificPopup"]').each(function(index, el) {
            var $el = $(this);

            $el.magnificPopup(magnificPopupDefault);
        });


        $('[data-init="magnificPopupVideo"]').each(function(index, el) {
            var $el = $(this);
            var option = {
                type: 'iframe',
                disableOn: 500,
                iframe: {
                    markup: '<div class="mfp-iframe-scaler">'+
                                '<div class="mfp-close"></div>'+
                                '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>'+
                                '</div>',    
                }
            }

            // Merge settings.
            var settings = $.extend(true, magnificPopupDefault, option);

            $el.magnificPopup(settings);
        });


        $('[data-init="magnificPopupInline"]').magnificPopup({
            type: 'inline',
            overflowY: 'scroll',
            fixedContentPos: true,
            preloader: false,
            showCloseBtn: true,
            closeOnContentClick: false,
            closeBtnInside: true,
            removalDelay: 500,
            callbacks: {
                beforeOpen: function() {
                    this.st.mainClass = 'mfp-zoom-in';
                }
            }
        });
    }

    function downLoadReportSlide() {
        $('.investorsDetail-featured .owl-carousel').owlCarousel({
            loop: true,
            items : 1,
            dots: true,
            nav : false,
            smartSpeed: 1500,
            pullDrag: false,
            margin: 20
        })
    }

    function productBlogSlide() {
        $('.sec-productBlog .owl-carousel').owlCarousel({
            loop: true,
            items : 1,
            dots: false,
            nav : true,
            smartSpeed: 1500,
            margin: 30,
            navText: ['<i class="fa fa-caret-left">', '<i class="fa fa-caret-right">'],
            responsive : {
                768 : {
                    items: 3
                },
                991 :{
                    items: 3,
                },
                1200 : {
                    items: 4,
                },
                1500 : {
                    items: 4,
                    margin: 50,
                }
            },
        })
    }

    function contactMap() {
        let map;
        var idMap = document.getElementById('mapContact');

        if(idMap) {
            const uluru = { lat: 21.018857, lng: 105.8399114 };

            const map = new google.maps.Map(idMap, {
                zoom: 18,
                center: uluru,
                disableDefaultUI: true,
                stylers: [
                    {
                        "featureType": "water",
                        "elementType": "geometry",
                        "stylers": [
                            {
                                "color": "#e9e9e9"
                            },
                            {
                                "lightness": 17
                            }
                        ]
                    },
                    {
                        "featureType": "landscape",
                        "elementType": "geometry",
                        "stylers": [
                            {
                                "color": "#f5f5f5"
                            },
                            {
                                "lightness": 20
                            }
                        ]
                    },
                    {
                        "featureType": "road.highway",
                        "elementType": "geometry.fill",
                        "stylers": [
                            {
                                "color": "#ffffff"
                            },
                            {
                                "lightness": 17
                            }
                        ]
                    },
                    {
                        "featureType": "road.highway",
                        "elementType": "geometry.stroke",
                        "stylers": [
                            {
                                "color": "#ffffff"
                            },
                            {
                                "lightness": 29
                            },
                            {
                                "weight": 0.2
                            }
                        ]
                    },
                    {
                        "featureType": "road.arterial",
                        "elementType": "geometry",
                        "stylers": [
                            {
                                "color": "#ffffff"
                            },
                            {
                                "lightness": 18
                            }
                        ]
                    },
                    {
                        "featureType": "road.local",
                        "elementType": "geometry",
                        "stylers": [
                            {
                                "color": "#ffffff"
                            },
                            {
                                "lightness": 16
                            }
                        ]
                    },
                    {
                        "featureType": "poi",
                        "elementType": "geometry",
                        "stylers": [
                            {
                                "color": "#f5f5f5"
                            },
                            {
                                "lightness": 21
                            }
                        ]
                    },
                    {
                        "featureType": "poi.park",
                        "elementType": "geometry",
                        "stylers": [
                            {
                                "color": "#dedede"
                            },
                            {
                                "lightness": 21
                            }
                        ]
                    },
                    {
                        "elementType": "labels.text.stroke",
                        "stylers": [
                            {
                                "visibility": "on"
                            },
                            {
                                "color": "#ffffff"
                            },
                            {
                                "lightness": 16
                            }
                        ]
                    },
                    {
                        "elementType": "labels.text.fill",
                        "stylers": [
                            {
                                "saturation": 36
                            },
                            {
                                "color": "#333333"
                            },
                            {
                                "lightness": 40
                            }
                        ]
                    },
                    {
                        "elementType": "labels.icon",
                        "stylers": [
                            {
                                "visibility": "off"
                            }
                        ]
                    },
                    {
                        "featureType": "transit",
                        "elementType": "geometry",
                        "stylers": [
                            {
                                "color": "#f2f2f2"
                            },
                            {
                                "lightness": 19
                            }
                        ]
                    },
                    {
                        "featureType": "administrative",
                        "elementType": "geometry.fill",
                        "stylers": [
                            {
                                "color": "#fefefe"
                            },
                            {
                                "lightness": 20
                            }
                        ]
                    },
                    {
                        "featureType": "administrative",
                        "elementType": "geometry.stroke",
                        "stylers": [
                            {
                                "color": "#fefefe"
                            },
                            {
                                "lightness": 17
                            },
                            {
                                "weight": 1.2
                            }
                        ]
                    }
                ]
            });
            const marker = new google.maps.Marker({
                position: uluru,
                icon: 'assets/img/marker-contact.png',
                map: map,
                title: 'Trụ sở Petrolimex',
            });

            marker.addListener("click", () => {
                infowindow.open(map, marker);
            });
        }
    }

    function postCategoryMasonryJs() {
        var wrap = $('.post-masonry');

        if (wrap.length ) {
            var inner = $('.grid-inner', wrap),
                item = $('.grid-item', wrap),
                sizer = $('.grid-sizer', wrap);

            inner.masonry({
                itemSelector: '.grid-item',
                columnWidth: '.grid-sizer',
                percentPosition: true
            })
        }
    }

    function countToJs() {
        var wrap = $('.countoJs');

        if( wrap.length ) {
            wrap.each(function() {
                var self = $(this),
                    dFrom = self.attr('data-from') ? self.attr('data-from') : 0,
                    dTo = self.attr('data-to') ? self.attr('data-to') : 1200,
                    dText = self.attr('data-text') ? self.attr('data-text') : '',
                    dBreak = self.attr('data-break') ? self.attr('data-break') : 'null';
 
                self.waypoint(function(direction) {
                    self.countTo({
                        speed: 1000,
                        refreshInterval: 50,
                        onUpdate: function (value) {
                            // console.debug(this);
                        },

                        formatter: function (value, options) {
                            value = value.toFixed(options.decimals);

                            if(options.decimals == 0 && value < 10) {
                                value = '0'+value;
                            }

                            if(dBreak != 'null') {
                                value = value.toString().replace('.', dBreak);
                            }
                            return value;
                        }
                    });

                    this.destroy();
                },{
                    offset: function(){
                        return Waypoint.viewportHeight() - self.outerHeight();
                    }
                });
            });
        }
    }

    function mapSearchJs() {
        function clickOpen() {
            var wrap = $('.sec-searchMap'),
                btnShowForm = $('.f-header__footer .btn-toggle', wrap);
            var clickbtn = false;
            btnShowForm.on('click', function(e) {
                $(this).closest('.f-header').find('.form-group').slideToggle();
                if( !clickbtn ) {
                    $(this).text($(this).attr('data-hide'));
                    clickbtn = true;
                }else {
                    $(this).text($(this).attr('data-show'));
                    clickbtn = false;
                }
            });
        }
        clickOpen();

        function map() {
            let map, infoWindow;
            var idMap = document.getElementById('map-js');

            if(idMap) {
                var dataInt = {
                    "markers": [
                        {
                            "lat": "20.8485499",
                            "lng": "106.6778597",
                            "name":"Petrolimex 1",
                            "address": "Số 625 Đê La Thành, Thành Công, Ba Đình, Hà Nội 1",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.846893",
                            "lng": "106.6799498",
                            "name":"Petrolimex 2",
                            "address": "Số 625 Đê La Thành, Thành Công, Ba Đình, Hà Nội 2",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.842253",
                            "lng": "106.6618125",
                            "name":"Petrolimex 3",
                            "address": "Số 625 Đê La Thành, Thành Công, Ba Đình, Hà Nội 3",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.876174",
                            "lng": "106.564917",
                            "name":"Petrolimex 4",
                            "address": "Số 625 Đê La Thành, Thành Công, Ba Đình, Hà Nội 4",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8430399",
                            "lng": "106.6601025",
                            "name":"Cửa Hàng Xăng Dầu Cầu Niệm - Petrolimex",
                            "address": "58 Trường Chinh, Quán Trữ, Kiến An, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8385496",
                            "lng": "106.6873811",
                            "name":"Cửa Hàng Xăng Dầu Ngô Gia Tự",
                            "address": "584 Ngô Gia Tự, Thành Tô, Hải An, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8376661",
                            "lng": "106.6822404",
                            "name":"Cửa Hàng Xăng Dầu Thiên Lôi",
                            "address": "Thiên Lôi, Đằng Giang, Ngô Quyền, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8510008",
                            "lng": "106.6728087",
                            "name":"Cửa Hàng Xăng Dầu Petrolimex Đình Vũ",
                            "address": "Phố Trần Hưng Đạo, Phường Đông Hải 2, Quận Hải An, Đông Hải 1, Hải An, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8465511",
                            "lng": "106.689192",
                            "name":"An Hai Petrolimex Petrol Store",
                            "address": "765, Nguyen Binh Khiem Street, Dong Hai Petrolimex Ward, Hai An District, Đông Hải 1, Hải An, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8495189",
                            "lng": "106.6337308",
                            "name":"An Dong Petrolimex Petrol Store",
                            "address": "Provincial Highway 208, Vinh Khue Hamlet, An Dong Commune, An Duong District, An Đông, An Dương, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8434332",
                            "lng": "106.687203",
                            "name":"Cửa Hàng Xăng Dầu Đồng Quốc Bình",
                            "address": "213 Lạch Tray, Đổng Quốc Bình, Ngô Quyền, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8338009",
                            "lng": "106.6706331",
                            "name":"Petrolimex Aviation Cat Bi",
                            "address": "Thành Tô, Hải An, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8532808",
                            "lng": "106.6715631",
                            "name":"Cửa Hàng Xăng Dầu Tam Bạc - Petrolimex",
                            "address": "Tam Bạc, Phạm Hồng Thái, Hồng Bàng, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8855845",
                            "lng": "106.6054607",
                            "name":"Cửa Hàng Xăng Dầu Quán Toan",
                            "address": "Hà Nội, Quán Toan, Hồng Bàng, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8650907",
                            "lng": "106.5698073",
                            "name":"Bac Ha Petrolimex Petrol Store",
                            "address": "Bac Ha Hamlet, Bac Son Commune, An Duong District, Bắc Sơn, An Dương, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.8689524",
                            "lng": "106.6215921",
                            "name":"Cửa Hàng Xăng Dầu Nam Sơn (Petrolimex)",
                            "address": "QL5, Hùng Vương, An Dương, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                        {
                            "lat": "20.87813",
                            "lng": "106.6220444",
                            "name":"Petrolimex - Cửa hàng 16",
                            "address": "12 Đường Hà Nội, Hùng Vương, Hồng Bàng, Hải Phòng, Việt Nam",
                            "phone": "(024) 38345566",
                            "mail": "chxd19.kv1@petrolimex.com.vn",
                            "work": "5:30 SA - 22:30 CH",
                            "icon": "images/icon/marker-contact.png"
                        },
                    ]
                }
    
                function initMap() {
                    const uluru = { lat: 20.8430747, lng: 106.6831592 };
                    const map = new google.maps.Map(idMap, {
                        zoom: 13,
                        center: uluru,
                        disableDefaultUI: true,
                    });
                    
                    const locationButton = document.querySelector('.f-map__location');
                    locationButton.addEventListener("click", () => {
                        infoWindow = new google.maps.InfoWindow();
                        
                        // Try HTML5 geolocation.
                        if (navigator.geolocation) {
                            navigator.geolocation.getCurrentPosition(
                                (position) => {
                                    const pos = {
                                        lat: position.coords.latitude,
                                        lng: position.coords.longitude,
                                    };
                                    // infoWindow.open(map);
                                    const marker = new google.maps.Marker({
                                        position: pos,
                                        icon: 'assets/img/icon-map-location.png',
                                        map: map,
                                    });
                                    
                                    map.setCenter(pos);
                                    infoWindow.setPosition(pos);
                                    infoWindow.setContent(`
                                        <div class="marker-item you-location">
                                            <h3 class="marker__name">Vị trí của bạn</h3>
                                        </div>
                                    `);
                                    infoWindow.open(map, marker);
                                },
                                () => {
                                    handleLocationError(true, infoWindow, map.getCenter());
                                }
                            );
                        } else {
                            handleLocationError(false, infoWindow, map.getCenter());
                        }
                    });
                    
    
                    // set map location
                    function contentString(name, address, phone, mail, work) {
                        return `
                            <div class="marker-item">
                                <h3 class="marker__name">${name}</h3>
                                <div class="marker__content">
                                    <ul>
                                        <li>
                                            <img src="assets/img/marker-icon-address.png" />
                                            ${address}
                                        </li>
                                        <li>
                                            <img src="assets/img/marker-icon-phone.png" />
                                            ${phone}
                                        </li>
                                        <li>
                                            <img src="assets/img/marker-icon-mail.png" />
                                            ${mail}
                                        </li>
                                        <li>
                                            <img src="assets/img/marker-icon-time.png" />
                                            ${work}
                                        </li>
                                    </ul>
                                <div>
                            </div>
                        `
                    }
                    
                    let marker, i;
                    let infoWindow2 = new google.maps.InfoWindow();
                    for(i = 0; i < dataInt.markers.length; i++) {
                        const pos = {
                            lat: Number(dataInt.markers[i].lat),
                            lng: Number(dataInt.markers[i].lng),
                        };
    
                        const _name = dataInt.markers[i].name,
                            _address = dataInt.markers[i].address,
                            _phone = dataInt.markers[i].phone,
                            _mail = dataInt.markers[i].mail,
                            _work = dataInt.markers[i].work;
                    
    
                        marker = new google.maps.Marker({
                            position: pos,
                            icon: 'assets/img/marker-contact.png',
                            map: map,
                        });
    
                        google.maps.event.addListener(marker, 'click', (function(marker, i) {
                            return function() {
                                var getLatLng = marker.getPosition();
                                infoWindow2.setPosition(pos);
                                infoWindow2.setContent(contentString(_name, _address, _phone, _mail, _work));
                                infoWindow2.open(map, marker);


                                // myLatLng = new google.maps.LatLng(lat, lon);
                                // marker.setPosition(getLatLng);
                                map.setZoom(15);
                                map.panTo(getLatLng); 
                                // map.setCenter(getLatLng);  
                                
                                // map.panTo(getLatLng);
                                // map.setCenter(getLatLng);;
                            }
                        })(marker, i));
                    }
                }
    
                initMap();
            }
        }
        map();
    }

    function scrollIdJs() {
        var scroll = new SmoothScroll('.sec-ctaPageLink a[href*="#"]', {
            speed: 1000,
	        speedAsDuration: true
        });

        var scroll = new SmoothScroll('.scrollId', {
            speed: 1000,
	        speedAsDuration: true
        });
    }

    function backtotopJs() {
        var id = $('#backtotop');
        var update = function() {
            var wh = $(window).height() / 2,
                scroll = $(window).scrollTop();
        
            if( scroll > wh ) {
                id.addClass('active');
            }else {
                id.removeClass('active');
            }
        }
        update();
        $(window).on('scroll', update);
        id.on('click', function (e) {
            e.preventDefault();
            $('html,body').animate({
                scrollTop: 0
            }, 700);
        });
    }

    function selectCustomJs() {
        $('.selectSearchJs').select2();

        $('.selectJs').select2({
            minimumResultsForSearch: Infinity
        });

    }
    
    function teamboxSelectJs() {
        var wrap =  $('.sec-teambox'),
            select = wrap.find('.selectJs'),
            panel = wrap.find('.sec-teambox__content .panel');

        select.on("select2:select", function (e) { 
            var select_val = $(e.currentTarget).val();
            
            panel.removeClass('active');
            wrap.find('#'+select_val).addClass('active');

        });
    }
    
    function dataImageMobileUrl() {
        if($(window).width() < 768) {
            $('[data-bg-mobile]').each(function() {
                var self = $(this),
                    url = self.attr('data-bg-mobile');

                if( url ) {
                    self.css('background-image', 'url('+url+')');
                }else {
                    self.css('background-color', '#0A54A8');
                }
            });
            
            $('[data-img-mobile]').each(function() {
                var self = $(this),
                    url = self.attr('data-img-mobile');
                    
                if( url ) {
                    self.attr('src', url);
                }
            });
        }else if($(window).width() > 767 && $(window).width() < 1199) {
            $('[data-bg-tablet]').each(function() {
                var self = $(this),
                    url = self.attr('data-bg-tablet');

                if( url ) {
                    self.css('background-image', 'url('+url+')');
                }else {
                    self.css('background-color', '#0A54A8');
                }                
            });

            $('[data-img-tablet]').each(function() {
                var self = $(this),
                    url = self.attr('data-img-tablet');
                    
                if( url ) {
                    self.attr('src', url);
                }
            });
        } else {
            $('[data-bg-pc]').each(function() {
                var self = $(this),
                    url = self.attr('data-bg-pc');

                if( url ) {
                    self.css('background-image', 'url('+url+')');
                }else {
                    self.css('background-color', '#0A54A8');
                }                
            });

            $('[data-img-pc]').each(function() {
                var self = $(this),
                    url = self.attr('data-img-pc');
                    
                if( url ) {
                    self.attr('src', url);
                        
                }
            });
        }
    }

    function industryCtaJs() {
        var slide  = $('.industry-cta__inner .owl-carousel');
        var fix = debounce(() => {
            var ww = $(window).width();

            if( ww < 768 ) {
                slide.owlCarousel('destroy');
            }else {
                slide.owlCarousel({
                    loop: true,
                    items : 3,
                    dots: false,
                    nav : true,
                    autoplay: true,
                    autoplayTimeout: 5000,
                    autoplayHoverPause: false,
                    smartSpeed: 1500,
                    margin: 0,
                    autoWidth: true,
                    navText: ['<i class="fa fa-caret-left">', '<i class="fa fa-caret-right">'],
                    touchDrag: false,
                    mouseDrag: false
                });
            }
        }, 100);
        fix();
        $(window).on('resize', fix);
    }

    function showLessJs() {
        var wrap = $('.showLess'),
            btnShow = wrap.find('.btn-show'),
            btnHide = wrap.find('.btn-up'),
            btnToogle = wrap.find('.btn-toggle'),
            content = wrap.find('.showLess__content');

        btnShow.on('click', function(e) {
            e.preventDefault();
            wrap.addClass('show-content');
            content.slideDown(300);
        });

        btnHide.on('click', function(e) {
            e.preventDefault();
            content.slideUp();
            setTimeout(function() {
                wrap.removeClass('show-content');
            }, 400);
        });

        btnToogle.on('click', function(e) {
            e.preventDefault();
            wrap.toggleClass('show-content');
            content.slideToggle();
        })
    }

    function getUrlScrollTo() {
        var hash = window.location.hash;
        var active = false;

        if($('.nav-tabs').find(`[href="${hash}"]`).length) {
            var update = function() {
                console.log(hash);
                $('.nav-tabs').find(`[href="${hash}"]`).on('click', function() {
                    if(active == false) {
                        var self = $(this),
                            offset = Math.floor(self.offset().top);
                        $('html, body').animate({scrollTop:offset}, 500);
                        active = true;
                    }
                });
                $('.nav-tabs').find(`[href="${hash}"]`).trigger('click');
            }
            update();   
            $('.menu-list').find('a').on('click', function() {
                var self = $(this);
                setTimeout(function() {
                    hash = window.location.hash;
                    active = false;
                    update();
                    $('.menu-list').find('.menu-has-children li').removeClass('menu-item-current');
                    self.parent().addClass('menu-item-current');
                }, 100);
            });
        }
    }

    function khoikdoanhSlideJs() {
        var wrap = $('.item-khoikdoanh__slide .owl-carousel');
        if(wrap.length) {
            wrap.each(function() {
                $(this).owlCarousel({
                    items: 1,
                    loop: true,
                    margin: 20,
                    dots: false,
                    smartSpeed: 1000,
                    animateIn: 'fadeIn',
                    animateOut: 'fadeOut',
                    autoplay: true,
                    autoplayTimeout: 5000,
                    autoplayHoverPause:true,
                    mouseDrag: false,
                    touchDrag: false,
                    nav: true,
                    navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>']
                })
            })
        }
    }

    // Call js
    dataImageMobileUrl();
    setTimeout(function() {
        wowJs();
    }, 200);
    headerJs();
    menuMobileJs();
    heroSlide();
    selectLanguageJs();
    copyToClipboard();
    btnShowMemberJs();
    // historyJs();
    ctaTextboxJs();
    businessResultsJs();
    upcomingEventSlideJs();
    collapseBoxJs();
    tabJs();
    popupJs();
    downLoadReportSlide();
    productBlogSlide();
    scrollIdJs();
    backtotopJs();
    selectCustomJs();
    industryCtaJs();
    showLessJs();
    teamboxSelectJs();
    khoikdoanhSlideJs();
    
    
    $(window).on('load', function() {
        $('body').addClass('body-load-done');
        $('[data-number-line]').numberTextLine();
        postCategoryMasonryJs();
        countToJs();
        contactMap();
        mapSearchJs();
        getUrlScrollTo();

        // var ww = $(window).width();
        // var hh = $(window).height();
        // $('.fixscreen').html(`width: ${ww}px <br> height: ${hh},<br> width2: ${ww/2}px <br> height2: ${hh/2}`);
    });
    
    jQuery(document).ready(function() {
        if( $('[data-youtube]').length ) {
            jQuery('[data-youtube]').youtube_background({
                mobile: true
            });
        }
    });
})(jQuery);
;(function($) {
	"use strict";

    function bctnTQLD() {
        var wrap = $('.sec-bctnTQLD .owl-carousel');
        if(wrap.length) {
            var owl = wrap.owlCarousel({
                items: 1,
                margin: 20,
                dots: false,
                smartSpeed: 1000,
                animateIn: 'fadeIn',
                animateOut: 'fadeOut',
                mouseDrag: false,
                touchDrag: false,
                nav: true,
                navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>']
            });
            
            $('.sec-bctnTQLD').find('.item-footer span').on('click', function() {
                $('.sec-bctnTQLD').find('.item-footer span').removeClass('active');
    
                if( $(this).hasClass('btn-next') ) {
                    owl.trigger('next.owl.carousel');
                    $(this).addClass('active')
                }else {
                    owl.trigger('prev.owl.carousel');
                    $(this).addClass('active')
                }
            });
        }
    }

    function bctnCCTC() {
        var wrap = $('.sec-bctnCCTC .owl-carousel');
        if(wrap.length) {
            var owl = wrap.owlCarousel({
                items: 1,
                margin: 20,
                dots: false,
                smartSpeed: 1000,
                nav: true,
                navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>']
            });
        }
    }

    function bctnTHCKKD() {
        var wrap = $('.sec-bctnTHCKKD .owl-carousel');
        if(wrap.length) {

            wrap.each(function() {
                var self = $(this);
                var owl = self.owlCarousel({
                    items: 1,
                    margin: 20,
                    dots: false,
                    smartSpeed: 1000,
                    nav: true,
                    navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>']
                });
            });
        }
    }


    function popupDetailCchdqt() {
        $('.click-popup').on('click', function(e) {
            e.preventDefault();
            var getId = $(this).attr('href');
            $(getId).addClass('show-popup');
        });

        $('.close-popup').on('click', function(e) {
            $(this).closest('.popup-detailCchdqt').removeClass('show-popup');
        });

        $('.popup-detailCchdqt .bg').on('click', function(e) {
            $(this).closest('.popup-detailCchdqt').removeClass('show-popup');
        });
    }

    function bctnCCHTKSNBJs() {
        var wrap = $('.sec-bctnCCHTKSNB .item-mb-slide .owl-carousel');
        if(wrap.length) {

            wrap.each(function() {
                var self = $(this);
                var owl = self.owlCarousel({
                    items: 1,
                    autoWidth: true,
                    margin: 15,
                    dots: true,
                    smartSpeed: 1000,
                    nav: false,
                    navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>']
                });
            });
        }
    }

    function bctnSlogan2MbSlide() {
        var wrap = $('.sec-bctnSlogan2 .item-mb-slide .owl-carousel');
        if(wrap.length) {

            wrap.each(function() {
                var self = $(this);
                var owl = self.owlCarousel({
                    items: 3,
                    autoWidth: true,
                    margin: 15,
                    dots: true,
                    smartSpeed: 1000,
                    nav: false,
                    navText: ['<i class="fa fa-caret-left"></i>','<i class="fa fa-caret-right"></i>']
                });
            });
        }
    }

    function popupCutomJs() {
        $('.click-popupJs').on('click', function(e) {
            e.preventDefault();
            var self = $(this);
            var getId = self.attr('href');

            if( $('.popup').hasClass('show-popup') ) {
                $('.popup').removeClass('show-popup');
            }
            $(getId).addClass('show-popup');
            $('body').addClass('body-fix-scroll');
        });

        $('.popup-close').on('click', function() {
            $(this).closest('.popup').removeClass('show-popup')
            $('body').removeClass('body-fix-scroll');
        });

        $('.popup__wrap').on('click', function() {
            $(this).closest('.popup').removeClass('show-popup')
            $('body').removeClass('body-fix-scroll');
        });

        $('.popup-dialog').on('click', function(e) {
            e.stopPropagation();
        });

        $('[data-popup-trigger]').on('click', function(e) {
            e.preventDefault();
            var getTrigger = $(this).attr('data-popup-trigger');
            console.log(getTrigger);

            $(this).closest('.popup').find(getTrigger).trigger('click');
        });
    }

    //
    bctnTQLD();
    bctnCCTC();
    bctnTHCKKD();
    popupDetailCchdqt();
    bctnCCHTKSNBJs();
    bctnSlogan2MbSlide();
    popupCutomJs();
})(jQuery);
;(function($) {
	"use strict";

    if (history.scrollRestoration) {
        history.scrollRestoration = 'manual';
        // history.scrollRestoration = 'auto';
    }

    const MathUtils = {
        // map number x from range [a, b] to [c, d]
        map: (x, a, b, c, d) => (x - a) * (d - c) / (b - a) + c,
        // linear interpolation
        lerp: (a, b, n) => (1 - n) * a + n * b,
        // Random float
        getRandomFloat: (min, max) => (Math.random() * (max - min) + min).toFixed(2)
    };


    function couterLineJs() {
        var wrap = $('.couterLineJs');

        if( wrap.length ) {
            wrap.each(function() {
                var self = $(this),
                    getPercent = self.attr('data-percent');

 
                self.waypoint(function(direction) {
                    TweenMax.to(self.find('.f-line')[0], 1, {xPercent: getPercent, x: '-100%', onUpdate: function() {
                        var getProgress = this.progress();

                        if( Math.floor(getProgress*10) > 2 && getPercent > 20 ) {
                           TweenMax.to(self[0], 0.2, {color: '#fff'});
                        }
                    } });

                    this.destroy();
                },{
                    offset: function(){
                        return Waypoint.viewportHeight() - self.outerHeight();
                    }
                });
            });
        }
    }

    function popupCutomJs() {
        $('.click-popupJs').on('click', function(e) {
            e.preventDefault();
            var self = $(this);
            var getId = self.attr('href');

            if( $('.popup').hasClass('show-popup') ) {
                $('.popup').removeClass('show-popup');
            }
            $(getId).addClass('show-popup');
            $('body').addClass('body-fix-scroll');
        });

        $('.popup-close').on('click', function() {
            $(this).closest('.popup').removeClass('show-popup')
            $('body').removeClass('body-fix-scroll');
        });

        $('.popup__bg').on('click', function() {
            $(this).closest('.popup').removeClass('show-popup')
            $('body').removeClass('body-fix-scroll');
        });

        $('[data-popup-trigger]').on('click', function(e) {
            e.preventDefault();
            var getTrigger = $(this).attr('data-popup-trigger');
            console.log(getTrigger);

            $(this).closest('.popup').find(getTrigger).trigger('click');
        });
    }

    function ptbvCSPT() {
        if( $('.sec-ptbvCSPT').length ) {
            var wrap = $('.sec-ptbvCSPT .item-animate')
            var inner = wrap.find('.item-animate__inner');
            var bg = inner.find('.bg');
    
            var getWidthWrap = wrap.width();
            var getWidthInner =  Math.floor(inner.width());
            var total = Math.floor(getWidthWrap+getWidthInner);
            TweenMax.to(bg[0], 50, {
                backgroundPosition: getWidthInner*-1+'px bottom',
                force3D:true,
                z:0.01,
                repeat:-1,
                rotation:0.01,
                //autoRound:false,
                ease: Linear.easeNone
            });

            var getW = $(window).width();
            var getCardA = getW + $('.sec-ptbvCSPT .car-a').width();
            var getCardB = getW + $('.sec-ptbvCSPT .car-b').width();
            var getCardC = getW + $('.sec-ptbvCSPT .car-c').width();
            var getCardD = getW + $('.sec-ptbvCSPT .car-d').width();

            TweenMax.set('.sec-ptbvCSPT .car-a span', {xPercent: -101, autoAlpha: 1});
            TweenMax.set('.sec-ptbvCSPT .car-b span', {xPercent: -101, autoAlpha: 1});
            TweenMax.set('.sec-ptbvCSPT .car-c span', {xPercent: 101, autoAlpha: 1});
            TweenMax.set('.sec-ptbvCSPT .car-d span', {xPercent: 101, autoAlpha: 1});

            var tl2 = new TimelineMax();
            tl2.addLabel('a')
            tl2.to('.sec-ptbvCSPT .car-a-1 span', 10, {x: getCardA, ease: Linear.easeNone, repeat: -1});
            tl2.to('.sec-ptbvCSPT .car-a-2 span', 12, {x: getCardA, ease: Linear.easeNone, repeat: -1}, 'a+=5');
            tl2.to('.sec-ptbvCSPT .car-b span', 20, {x: getCardB, ease: Linear.easeNone, repeat: -1}, 'a+=2');
            tl2.to('.sec-ptbvCSPT .car-c span', 7, {x: -getCardC, ease: Linear.easeNone, repeat: -1}, 'a+=5');
            tl2.to('.sec-ptbvCSPT .car-d span', 9, {x: -getCardD, ease: Linear.easeNone, repeat: -1}, 'a+=8');
        }
    }

    function ptbvVDTYJs() {
        if( $('.sec-ptbvVDTY').length ) {
            var getWW = $(window).width();
            var getH = $('.sec-ptbvVDTY').outerHeight();
            var _delay = [400, 700];
            var _dur = [20,30];
            var _rev = [1,-1];
            
            var item1 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-1').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-1 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item1();
                    }});
                },_delay[1]);
            }
            item1();
    
            var item2 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-2').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-2 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item2();
                    }});
                },_delay[_set]);
            }
            item2();
    
            var item3 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-3').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-3 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item3();
                    }});
                },_delay[_set]);
            }
            item3();
    
            var item4 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-4').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-4 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item4();
                    }});
                },_delay[_set]);
            }
            item4();
    
            var item5 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-5').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-5 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item5();
                    }});
                },_delay[_set]);
            }
            item5();
    
            var item6 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-6').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-6 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item6();
                    }});
                },_delay[_set]);
            }
            item6();
    
            var item7 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-7').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-7 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item7();
                    }});
                },_delay[_set]);
            }
            item7();
    
            var item8 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-8').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-8 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item8();
                    }});
                },_delay[_set]);
            }
            item8();
    
            var item9 = function() {
                var randomX = MathUtils.getRandomFloat(100, 200);
                var getHH = (getH + $('.sec-ptbvVDTY .sharp-9').height())*-1;
                var _set = Math.round(MathUtils.getRandomFloat(0, 1));
                setTimeout(function() {
                    TweenMax.fromTo('.sec-ptbvVDTY .sharp-9 span', _dur[_set], {y: 0, x: 0}, {y: getHH, x: randomX*_rev[_set], onUpdate: function() {
                    }, onComplete: function() {
                        item9();
                    }});
                },_delay[_set]);
            }
            item9();
        }
    }

    function ptbvCLPTBV() {
        var wrap =  $('.sec-ptbvCLPTBV');
        if( wrap.length ) {
            TweenMax.set('.sec-ptbvCLPTBV .layer-1', {scaleY: 0, transformOrigin: '50% 100%', autoAlpha: 1});
            TweenMax.set('.sec-ptbvCLPTBV .layer-2', {scale: 0, transformOrigin: 'center center', autoAlpha: 1});
            TweenMax.set('.sec-ptbvCLPTBV .layer-3', {scale: 0, transformOrigin: 'center center', autoAlpha: 1});
            TweenMax.set('.sec-ptbvCLPTBV .text-1', {xPercent: 50, autoAlpha: 0});
            TweenMax.set('.sec-ptbvCLPTBV .text-2', {xPercent: 50, autoAlpha: 0});
            TweenMax.set('.sec-ptbvCLPTBV .layer-4', {scaleX: 0, transformOrigin: '100% 50%', autoAlpha: 1});

            var tl = new TimelineMax({paused: true});
            tl.to('.sec-ptbvCLPTBV .line path', 0.5, {strokeDashoffset: 1965, ease: Linear.easeNone});
            tl.addLabel('a')
            tl.to('.sec-ptbvCLPTBV .layer-1', 1, {scaleY: 1, ease: Elastic.easeOut.config(1, 0.3)});
            tl.to('.sec-ptbvCLPTBV .line path', 1, {strokeDashoffset: 1700, ease: Linear.easeNone}, 'a');
            tl.addLabel('b')
            tl.to('.sec-ptbvCLPTBV .layer-2', 1, {scale: 1, ease: Elastic.easeOut.config(1, 0.3)});
            tl.to('.sec-ptbvCLPTBV .text-1', 0.5, {xPercent: 0, autoAlpha: 1}, 'b+=0.5');
            tl.to('.sec-ptbvCLPTBV .line path', 1, {strokeDashoffset: 720, ease: Linear.easeNone}, 'b');
            tl.addLabel('c')
            tl.to('.sec-ptbvCLPTBV .layer-3', 1, {scale: 1, ease: Elastic.easeOut.config(1, 0.3)});
            tl.to('.sec-ptbvCLPTBV .text-2', 0.5, {xPercent: 0, autoAlpha: 1}, 'c+=0.5');
            tl.to('.sec-ptbvCLPTBV .line path', 1, {strokeDashoffset: 280, ease: Linear.easeNone}, 'c');
            tl.addLabel('d');
            tl.to('.sec-ptbvCLPTBV .layer-4', 1, {scaleX: 1, ease: Elastic.easeOut.config(1, 0.3)});
            tl.to('.sec-ptbvCLPTBV .line path', 1, {strokeDashoffset: 0, ease: Linear.easeNone}, 'd');

            ScrollTrigger.create({
                trigger: ".sec-ptbvCLPTBV .item-anime",
                start: "top bottom",
                end: "bottom bottom",
                // markers: true,
                once: true,
                onToggle: self => {
                    tl.play();
                },
            });
            

            var getW = $(window).width();
            var getCardA = getW + $('.sec-ptbvCLPTBV .car-a').width();
            var getCardB = getW + $('.sec-ptbvCLPTBV .car-b').width();
            var getCardCStop = (getW / 3) + $('.sec-ptbvCLPTBV .car-c').width();
            var getCardC = getW + $('.sec-ptbvCLPTBV .car-c').width();

            TweenMax.set('.sec-ptbvCLPTBV .car-a span', {xPercent: -101, autoAlpha: 1});
            TweenMax.set('.sec-ptbvCLPTBV .car-b span', {xPercent: -101, autoAlpha: 1});
            TweenMax.set('.sec-ptbvCLPTBV .car-c span', {xPercent: -101, autoAlpha: 1});

            var tl2 = new TimelineMax();
            tl2.addLabel('a')
            tl2.to('.sec-ptbvCLPTBV .car-a-1 span', 10, {x: getCardA, ease: Linear.easeNone, repeat: -1});
            tl2.to('.sec-ptbvCLPTBV .car-a-2 span', 10, {x: getCardA, ease: Linear.easeNone, repeat: -1}, 'a+=5');

            if( $(window).width() > 767 ) {
                tl2.to('.sec-ptbvCLPTBV .car-b-1 span', 20, {x: getCardB, ease: Linear.easeNone, repeat: -1}, 'a+=2');
                tl2.to('.sec-ptbvCLPTBV .car-b-2 span', 25, {x: getCardB, ease: Linear.easeNone, repeat: -1}, 'a+=8');
            }else {
                getCardCStop = (getW / 2);
            }


            var tl3 = new TimelineMax({repeat: -1});
            tl3.to('.sec-ptbvCLPTBV .car-c span', 5, {x: getCardCStop, ease: Linear.easeNone}, '+=3');
            tl3.to('.sec-ptbvCLPTBV .car-c span', 5, {x: getCardC}, '+=3');
        }
    }

    function ptbvCLSPXJs() {
        var wrap = $('.sec-ptbvCLSPX');
        if( wrap.length ) {
            wrap.find('.accordion__title').on('click', function() {
                if( $(this).closest('.accordion__item').hasClass('active') ) {
                    $(this).closest('.accordion__item').removeClass('active');
                }else {
                    $(this).closest('.accordion').find('.accordion__item').removeClass('active');
                    $(this).closest('.accordion__item').addClass('active');
                }
            });
        }
    }

    function ptbvKTGTJs() {
        var wrap = $('.sec-ptbvKTGT');
        if( wrap.length ) {
            $('.sec-ptbvKTGT .btn-show').on('click', function(e) {
                e.preventDefault();
                $('.sec-ptbvKTGT .item-lessShow').addClass('showed');
            });
            $('.sec-ptbvKTGT .btn-less').on('click', function(e) {
                e.preventDefault();
                $('.sec-ptbvKTGT .item-lessShow').removeClass('showed');
            });
        }
    }

    //
    couterLineJs();
    popupCutomJs();
    ptbvCSPT();
    ptbvCLSPXJs();
    ptbvKTGTJs();

    $(window).on('load', function() {
        ptbvVDTYJs();
        ptbvCLPTBV();
    });
})(jQuery);
;__vieapps.prices = {
	time: undefined,
	products: [],
	zone2URL: "https://www.petrolimex.com.vn/vung-2.html",
	stationsURL: "https://www.petrolimex.com.vn/stations.html",
	fetch: function (callback, sortBy, pagination) {
		__vieapps.apis.fetch("portals", "cms.item", "search", undefined, {
			"x-request": __vieapps.crypto.jsonEncode({
				FilterBy: {
					And: [
						{
							SystemID: {
								Equals: "6783dc1271ff449e95b74a9520964169"
							}
						},
						{
							RepositoryID: {
								Equals: "a95451e23b474fe5886bfb7cf843f53c"
							}
						},
						{
							RepositoryEntityID: {
								Equals: "3801378fe1e045b1afa10de7c5776124"
							}
						},
						{
							Status: {
								Equals: "Published"
							}
						}
					]
				},
				SortBy: sortBy || { LastModified: "Descending" },
				Pagination: pagination || {
					TotalRecords: -1,
					TotalPages: 0,
					PageSize: 0,
					PageNumber: 0
				}
			})
		}, data => {
			this.products = this.map(data.Objects);
			var time = this.getLastModifiedTime();
			localStorage.setItem("prices", JSON.stringify({
				time: time,
				products: this.products
			}));
			if (typeof callback === "function") {
				callback(time);
			}
		})
	},
	map: items => (items || []).map(item => ({
		ID: item.ID,
		Title: item.Title,
		EnglishTitle: item.EnglishTitle,
		Link: item.Link,
		Zone1Price: item.Zone1Price,
		Zone2Price: item.Zone2Price,
		OrderIndex: item.DIsplayOrder !== undefined ? +item.DIsplayOrder : +item.OrderIndex,
		LastModified: new Date(item.LastModified)
	})),
	getLastModifiedTime: function () {
		return this.products.sortBy({ name: "LastModified", reverse: true }).first().LastModified;
	},
	getUpdatedTime: function () {
		var time = new Date(this.time);
		var hours = time.getHours();
		var minutes = time.getMinutes();
		if (minutes > 50) {
			hours++;
			if (hours > 24) {
				hours = 0;
			}
			minutes = 0;
		}
		else {
			/*
			hours = hours > 13 && hours < 17
				? 15
				: hours >= 17 && hours < 19
					? 17
					: hours >= 19 && hours < 21
						? 19
						: hours;
			*/
			minutes = minutes >= 45
				? 45
				: minutes >= 30
					? 30
					: minutes >= 15 ? 15 : 0;
		}
		time.setHours(hours);
		time.setMinutes(minutes);
		return time;
	},
	header: function () {
		return `<thead><tr>
		<th>${(__vieapps.language == "vi-VN" ? "Sản phẩm" : "Product")}</th>
		<th>${(__vieapps.language == "vi-VN" ? "Vùng 1" : "Zone 1")}</th>
		<th>${(__vieapps.language == "vi-VN" ? "<a href=\"" + this.zone2URL + "\" target=\"_blank\">Vùng 2</a>" : "Zone 2")}</th>
		</tr></thead>`;
	},
	footer: function () {
		var time = this.getUpdatedTime();
		return `<p class="f-info"><span>*${(__vieapps.language == "vi-VN" ? "đơn vị" : "unit")}: VND</span>
			${(__vieapps.language == "vi-VN" ? "Giá của Petrolimex cập nhật lúc" : "Updated at")}
			&nbsp;${__vieapps.utils.time.getFriendly(time)}</p>`;
	},
	show: function (selector, forMobile, dontAddHeaders, callback) {
		var html = "";
		if (!dontAddHeaders) {
			html += `<a href="#" class="f-btn">${(__vieapps.language == "vi-VN" ? "Giá bán lẻ xăng dầu" : "Retail prices")}</a>
				${(!!forMobile ? `<div class="f-bg"></div>` : "")}
				<div class="f-list"><table>${this.header()}<tbody>`;
		}
		this.products.sortBy("OrderIndex").map(product => ({
			Title: __vieapps.language == "vi-VN" ? product.Title : product.EnglishTitle,
			Link: !!product.Link && product.Link != "#" ? `<a href="${product.Link}" target="_blank">` : "",
			Zone1Price: product.Zone1Price.toLocaleString(__vieapps.language),
			Zone2Price: product.Zone2Price.toLocaleString(__vieapps.language)
		})).forEach(product => html += `<tr><td>${product.Link}${product.Title}${!!product.Link ? "</a>" : ""}</td><td>${product.Zone1Price}</td><td>${product.Zone2Price}</td></tr>`);
		if (!dontAddHeaders) {
			html += `</tbody></table>${this.footer()}${(!forMobile ? `<a href="${this.stationsURL}" target="_blank" class="btn f-search"><img src="${__vieapps.URLs.portals}/_themes/sunrise/img/icon-location.svg"/> ${(__vieapps.language == "vi-VN" ? "Tìm kiếm cây xăng quanh bạn" : "Search for gas stations")}</a>` : "")}`;
		}
		$(selector).html(html);
		if (typeof callback === "function") {
			callback();
		}
	},
	showPrices: function (selector, forMobile, dontAddHeaders, callback) {
		if (!!this.time) {
			this.show(selector, forMobile, dontAddHeaders, callback);
		}
		else {
			this.fetch(() => this.show(selector, forMobile, dontAddHeaders, callback));
		}
	},
	init: function (callback) {
		var prices = JSON.parse(localStorage.getItem("prices") || "{}");
		this.products = this.map(prices.products);
		this.time = !!prices.time ? new Date(prices.time) : undefined;
		if (!!!this.time || !!!this.products.length || !!this.products.filter(product => !!!product.Zone1Price || !!!product.Zone2Price).length) {
			localStorage.removeItem("prices");
			this.fetch(time => {
				this.time = time;
				if (typeof callback === "function") {
					callback();
				}
			});
		}
		else {
			setTimeout(() => this.fetch(time => {
				if (typeof callback === "function" && __vieapps.utils.time.diff(this.time, time) != 0) {
					this.time = time;
					callback();
				}
			}), 2345);
			if (typeof callback === "function") {
				callback();
			}
		}
	}
};
showPrices = (selector, forMobile, dontAddHeaders, callback) => __vieapps.prices.show(selector, forMobile, dontAddHeaders, callback);
showRetailPrices = (selector, forMobile, dontAddHeaders, callback) => __vieapps.prices.init(() => showPrices(selector, forMobile, dontAddHeaders, callback));
$(() => __vieapps.prices.init(() => showPrices(".header__pricePetrol", false, false, () => showPrices(".menu-mobile__pricePetrol", true, false, () => {
	$(".header__pricePetrol a[href='#'], .menu-mobile__pricePetrol a[href='#'], nav.header__nav a[href='#'], nav.menu-mobile__nav a[href='#']").on("click tap", event => event.preventDefault());
	$(".menu-mobile__pricePetrol .f-btn, .menu-mobile__pricePetrol .f-bg").on("click tap", event => {
		event.preventDefault();
		$(event.currentTarget).parent().toggleClass("active");
	});
}))));

;__vieapps.stock = {
	time: undefined,
	data: undefined,
	fetch: function (callback) {
		__vieapps.apis.fetch("indexes", "stock", "plx", undefined, undefined, function (data) {
			__vieapps.stock.time = new Date();
			__vieapps.stock.data = data;
			localStorage.setItem("stock", JSON.stringify({
				time: __vieapps.stock.time,
				data: __vieapps.stock.data
			}));
			if (typeof callback === "function") {
				callback();
			}
		});
	},
	init: function () {
		var stock = JSON.parse(localStorage.getItem("stock") || "{}");
		__vieapps.stock.time = !!stock.time ? new Date(stock.time) : undefined;
		__vieapps.stock.data = stock.data;
		if (__vieapps.stock.time === undefined || __vieapps.utils.time.diff(__vieapps.stock.time) > 7) {
			__vieapps.stock.fetch();
		}
	},
	show: function (priceSelector, changeSelector, timeSelector) {
		var time = new Date(__vieapps.stock.data.Info.Date);
		$(priceSelector).text(__vieapps.stock.data.Prices.Current);
		$(changeSelector).html(`${__vieapps.stock.data.Changes.Percent} <i class="fa fa-caret-${__vieapps.stock.data.Changes.Type} ${__vieapps.stock.data.Changes.Type}"></i>`);
		$(timeSelector).text(`${(__vieapps.language == "vi-VN" ? "Cập nhật lần cuối lúc" : "Updated at")} ${__vieapps.utils.time.getFriendly(time)}`);
	}
};
$(function () {
	__vieapps.stock.init();
});
var showStock = function (priceSelector, changeSelector, timeSelector) {
	if (__vieapps.stock.time) {
		__vieapps.stock.show(priceSelector, changeSelector, timeSelector);
	}
	else {
		__vieapps.stock.fetch(function () {
			__vieapps.stock.show(priceSelector, changeSelector, timeSelector);
		});
	}
};

;__vieapps.reports = {
	vi: {
		time: undefined,
		data: [],
		filterBy: {
			And: [
				{
					SystemID: {
						Equals: "6783dc1271ff449e95b74a9520964169"
					}
				},
				{
					RepositoryID: {
						Equals: "a95451e23b474fe5886bfb7cf843f53c"
					}
				},
				{
					RepositoryEntityID: {
						Equals: "81ec1fdd97264b8e9f50d9fbdb8b8dcc"
					}
				},
				{
					Status: {
						Equals: "Published"
					}
				}
			]
		}
	},
	en: {
		time: undefined,
		data: [],
		filterBy: {
			And: [
				{
					SystemID: {
						Equals: "6783dc1271ff449e95b74a9520964169"
					}
				},
				{
					RepositoryID: {
						Equals: "a95451e23b474fe5886bfb7cf843f53c"
					}
				},
				{
					RepositoryEntityID: {
						Equals: "074ec0d5f2f044748c2ba2c9f17f0792"
					}
				},
				{
					Status: {
						Equals: "Published"
					}
				}
			]
		}
	},
	fetch: function (callback, reports, filterBy, sortBy, pagination) {
		__vieapps.apis.fetch(
			"portals",
			"cms.item",
			"search",
			undefined,
			{
				"x-request": __vieapps.crypto.jsonEncode({
					FilterBy: filterBy,
					SortBy: sortBy || { Created: "Ascending" },
					Pagination: pagination || {
						TotalRecords: -1,
						TotalPages: 0,
						PageSize: 100,
						PageNumber: 0
					}
				}),
				"ShowAttachments": "x"
			},
			function (data) {
				reports.data = reports.data.merge(__vieapps.reports.map(data.Objects))
					.distinct((value, index, array) => array.findIndex(val => val.ID == value.ID) == index)
					.sortBy({ name: "AnnouncedDate", reverse: true }, { name: "Title" });
				if (typeof callback === "function") {
					callback(data);
				}
			}
		);
	},
	fetchAll: function (reports, filterBy, pagination, callback, stepCallback) {
		this.fetch(function (data) {
			if (typeof stepCallback === "function") {
				stepCallback(data);
			}
			pagination = data.Pagination;
			pagination.PageNumber++;
			if (pagination.PageNumber <= pagination.TotalPages) {
				setTimeout(function () {
					__vieapps.reports.fetchAll(reports, filterBy, pagination, callback, stepCallback);
				}, 13);
			}
			else {
				__vieapps.reports.store();
				if (typeof callback === "function") {
					callback(data);
				}
			}
		}, reports, filterBy, undefined, pagination);
	},
	map: function (items) {
		return (items || []).map(item => {
			var url = typeof item.DocumentURL === "string" && item.DocumentURL.trim() !== ""
				? item.DocumentURL
				: item.Attachments && item.Attachments.length
					? item.Attachments.first().URIs.Direct
					: item.URL || __vieapps.URLs.portals;
			return {
				ID: item.ID,
				Title: item.Title,
				DocumentType: item.DocumentType,
				Year: +item.Year,
				URL: url,
				EBookURL: item.EBookURL,
				EDocumentURL: item.EDocumentURL,
				AnnouncedDate: new Date(item.AnnouncedDate),
				Created: new Date(item.Created),
				LastModified: new Date(item.LastModified)
			};
		});
	},
	store: function () {
		__vieapps.reports.vi.time = __vieapps.reports.vi.data.length
			? __vieapps.reports.vi.data.sortBy({ name: "LastModified", reverse: true }).first().LastModified
			: undefined;
		__vieapps.reports.en.time = __vieapps.reports.en.data.length
			? __vieapps.reports.en.data.sortBy({ name: "LastModified", reverse: true }).first().LastModified
			: undefined;
		localStorage.setItem("reports", JSON.stringify({
			vi: {
				time: __vieapps.reports.vi.time,
				data: __vieapps.reports.vi.data
			},
			en: {
				time: __vieapps.reports.en.time,
				data: __vieapps.reports.en.data
			}
		}));
	},
	show: function (listSelector, paginationSelector, reports, documentType, year, page, callback) {
		page = page != undefined && +page > 0 ? +page : 1;
		year = year != undefined ? year == "all" || +year < 0 ? -1 : +year : 0;
		year = year > 0 ? year : year < 0 ? 0 : __vieapps.paginator.handlers[`${documentType}:year`] || 0;
		__vieapps.paginator.handlers[`${documentType}:year`] = year;
		reports = reports.filter(report => report.DocumentType == documentType);
		if (year > 0) {
			reports = reports.filter(report => report.Year == year);
		}
		if (!__vieapps.paginator.handlers[documentType]) {
			__vieapps.paginator.handlers[documentType] = function (pageNumber) {
				__vieapps.reports.show(listSelector, paginationSelector, reports, documentType, year, pageNumber);
			};
		}
		var html = "";
		var size = 7;
		reports.sortBy({ name: "AnnouncedDate", reverse: true }, { name: "Title" })
			.take(size, (page - 1) * size)
			.forEach(report => html += `
			<li class="item">
				<div class="item__body">
					<div class="row">
						<div class="col-lg-8 col-xl-9">
							<h3 class="item__title"><a href="${report.URL}" target="_blank">${report.Title}</a></h3>
						</div>
						<div class="col-lg-4 col-xl-3">
							<div class="item__meta text-lg-right"><span>${report.AnnouncedDate.toLocaleDateString(__vieapps.language)}</span></div>
						</div>
						<a href="${report.URL}" target="_blank" class="item__btn">
							<span>Download</span>
							<svg xmlns="http://www.w3.org/2000/svg" width="10.5" height="10.5" viewBox="0 0 10.5 10.5">
								<path id="Shape" d="M0,10V9.1H10V10ZM1.535,4.738,2.172,4.1,4.549,6.478V0h.9V6.478L7.828,4.1l.637.637L5,8.2Z" transform="translate(0.25 0.25)" fill="#0A54A8" stroke="#0A54A8" stroke-miterlimit="10" stroke-width="0.5"></path>
							</svg>
						</a>
					</div>
				</div>
			</li>`);
		$(listSelector).html(html);
		__vieapps.paginator.show(paginationSelector, documentType, page, size, reports.length, true, 7);
		if (typeof callback === "function") {
			callback();
		}
	}
};
$(function () {
	var reports = JSON.parse(localStorage.getItem("reports") || "{\"vi\":{},\"en\":{}}");
	__vieapps.reports.vi.time = !!reports.vi.time ? new Date(reports.vi.time) : undefined;
	__vieapps.reports.vi.data = __vieapps.reports.map(reports.vi.data).sortBy({ name: "AnnouncedDate", reverse: true }, { name: "Title" });
	if (!!__vieapps.reports.vi.time) {
		setTimeout(function () {
			__vieapps.reports.fetch(
				function (data) {
					if (data.Objects.length && __vieapps.utils.time.diff(__vieapps.reports.vi.time, data.Objects.first().LastModified) > 0) {
						__vieapps.reports.vi.data = [];
						__vieapps.reports.fetchAll(__vieapps.reports.vi, __vieapps.reports.vi.filterBy);
					}
				},
				__vieapps.reports.vi,
				__vieapps.reports.vi.filterBy,
				{
					LastModified: "Descending"
				},
				{
					TotalRecords: -1,
					TotalPages: 0,
					PageSize: 1,
					PageNumber: 0
				}
			);
		}, 2345);
	}
	else {
		__vieapps.reports.fetchAll(__vieapps.reports.vi, __vieapps.reports.vi.filterBy);
	}
	__vieapps.reports.en.time = !!reports.en.time ? new Date(reports.en.time) : undefined;
	__vieapps.reports.en.data = __vieapps.reports.map(reports.en.data).sortBy({ name: "AnnouncedDate", reverse: true }, { name: "Title" });
	if (!!__vieapps.reports.en.time) {
		setTimeout(function () {
			__vieapps.reports.fetch(
				function (data) {
					if (data.Objects.length && __vieapps.utils.time.diff(__vieapps.reports.en.time, data.Objects.first().LastModified) > 0) {
						__vieapps.reports.en.data = [];
						__vieapps.reports.fetchAll(__vieapps.reports.en, __vieapps.reports.en.filterBy);
					}
				},
				__vieapps.reports.en,
				__vieapps.reports.en.filterBy,
				{
					LastModified: "Descending"
				},
				{
					TotalRecords: -1,
					TotalPages: 0,
					PageSize: 1,
					PageNumber: 0
				}
			);
		}, 2345);
	}
	else {
		__vieapps.reports.fetchAll(__vieapps.reports.en, __vieapps.reports.en.filterBy);
	}
});

;__vieapps.faqs = {
	vi: {
		time: undefined,
		data: [],
		categories: ["b23d677c00a24fec86c9b26bb7934e0f", "f3446e0a0f6b49159759120adc3d4037", "b4dcfdab4424461daa0f6d25c57262db", "42c2f456369f475b9236c9c3647c3d3d"],
		fetch: function (callback, filter, sort, pagination) {
			var request = {
				FilterBy: {
					And: [
						{
							SystemID: {
								Equals: "6783dc1271ff449e95b74a9520964169"
							}
						},
						{
							RepositoryID: {
								Equals: "a95451e23b474fe5886bfb7cf843f53c"
							}
						},
						{
							RepositoryEntityID: {
								Equals: "0d4f635fb0cf4a1b822db35e5bb1ef6e"
							}
						},
						{
							Status: {
								Equals: "Published"
							}
						}
					]
				},
				SortBy: sort || { Created: "Ascending" },
				Pagination: pagination || {
					TotalRecords: -1,
					TotalPages: 0,
					PageSize: 10,
					PageNumber: 0
				}
			};
			if (typeof filter === "object" && filter !== undefined && filter !== null) {
				request.FilterBy.And.push(filter);
			}
			__vieapps.apis.fetch("portals", "cms.content", "search", undefined, { "x-request": __vieapps.crypto.jsonEncode(request), "ShowURLs": "x" }, function (data) {
				__vieapps.faqs.vi.data = __vieapps.faqs.vi.data.concat(__vieapps.faqs.map(data.Objects)).distinct((value, index, array) => array.findIndex(val => val.ID == value.ID) == index).sortBy({ name: "PublishedTime", reverse: true }, { name: "LastModified", reverse: true });
				if (typeof callback === "function") {
					callback(data);
				}
			});
		},
		fetchByCategory: function (categoryID, pagination, callback, stepCallback) {
			__vieapps.faqs.vi.fetch(
				function (data) {
					if (typeof stepCallback === "function") {
						stepCallback(data);
					}
					pagination = data.Pagination;
					pagination.PageNumber++;
					if (pagination.PageNumber <= pagination.TotalPages) {
						setTimeout(function () {
							__vieapps.faqs.vi.fetchByCategory(categoryID, pagination, callback, stepCallback);
						}, 13);
					}
					else if (typeof callback === "function") {
						callback(data);
					}
				},
				{
					CategoryID: {
						Equals: categoryID
					}
				},
				undefined,
				pagination
			);
		},
		show: function (selector, categoryID, callback) {
			if (__vieapps.faqs.vi.data.length) {
				__vieapps.faqs.show(__vieapps.faqs.vi.data, selector, categoryID, callback);
			}
			else {
				__vieapps.faqs.vi.fetchByCategory(categoryID, undefined, function () {
					__vieapps.faqs.show(__vieapps.faqs.vi.data, selector, categoryID, callback);
					__vieapps.faqs.vi.categories.forEach(categoryID => __vieapps.faqs.vi.fetchByCategory(categoryID));
				});
			}
		}
	},
	en: {
		time: undefined,
		data: [],
		categories: ["dc7de50ef0d2457aa06065cf9948d6a6", "38a468473efc406cac1587f09777c2f9", "dbf3bb539c06446b927ecee242ef5b8d", "2d8a40119b764a93a72c808fda1bdfb9"],
		fetch: function (callback, filter, sort, pagination) {
			var request = {
				FilterBy: {
					And: [
						{
							SystemID: {
								Equals: "6783dc1271ff449e95b74a9520964169"
							}
						},
						{
							RepositoryID: {
								Equals: "2ac0596cba1e4c5e8eb943024d7af0c9"
							}
						},
						{
							RepositoryEntityID: {
								Equals: "9a3a0564573a4b45a752a9a4d71ea0b3"
							}
						},
						{
							Status: {
								Equals: "Published"
							}
						}
					]
				},
				SortBy: sort || { Created: "Ascending" },
				Pagination: pagination || {
					TotalRecords: -1,
					TotalPages: 0,
					PageSize: 10,
					PageNumber: 0
				}
			};
			if (typeof filter === "object" && filter !== undefined && filter !== null) {
				request.FilterBy.And.push(filter);
			}
			__vieapps.apis.fetch("portals", "cms.content", "search", undefined, { "x-request": __vieapps.crypto.jsonEncode(request), "ShowURLs": "x" }, function (data) {
				__vieapps.faqs.en.data = __vieapps.faqs.en.data.concat(__vieapps.faqs.map(data.Objects)).distinct((value, index, array) => array.findIndex(val => val.ID == value.ID) == index).sortBy({ name: "PublishedTime", reverse: true }, { name: "LastModified", reverse: true });
				if (typeof callback === "function") {
					callback(data);
				}
			});
		},
		fetchByCategory: function (categoryID, pagination, callback, stepCallback) {
			__vieapps.faqs.en.fetch(
				function (data) {
					if (typeof stepCallback === "function") {
						stepCallback(data);
					}
					pagination = data.Pagination;
					pagination.PageNumber++;
					if (pagination.PageNumber <= pagination.TotalPages) {
						setTimeout(function () {
							__vieapps.faqs.en.fetchByCategory(categoryID, pagination, callback, stepCallback);
						}, 13);
					}
					else if (typeof callback === "function") {
						callback(data);
					}
				},
				{
					CategoryID: {
						Equals: categoryID
					}
				},
				undefined,
				pagination
			);
		},
		show: function (selector, categoryID, callback) {
			if (__vieapps.faqs.en.data.length) {
				__vieapps.faqs.show(__vieapps.faqs.en.data, selector, categoryID, callback);
			}
			else {
				__vieapps.faqs.en.fetchByCategory(categoryID, undefined, function () {
					__vieapps.faqs.show(__vieapps.faqs.en.data, selector, categoryID, callback);
					__vieapps.faqs.en.categories.forEach(categoryID => __vieapps.faqs.en.fetchByCategory(categoryID));
				});
			}
		}
	},
	map: function (items) {
		return (items || []).map(item => {
			return {
				ID: item.ID,
				Title: item.Title,
				CategoryID: item.CategoryID,
				OtherCategories: item.OtherCategories || [],
				RepositoryEntityID: item.RepositoryEntityID,
				URL: item.URL,
				PublishedTime: new Date(item.PublishedTime),
				Created: new Date(item.Created),
				LastModified: new Date(item.LastModified)
			};
		});
	},
	store: function () {
		__vieapps.faqs.vi.time = __vieapps.faqs.vi.data.length
			? __vieapps.faqs.vi.data.sortBy({ name: "LastModified", reverse: true }).first().LastModified
			: undefined;
		__vieapps.faqs.en.time = __vieapps.faqs.en.data.length
			? __vieapps.faqs.en.data.sortBy({ name: "LastModified", reverse: true }).first().LastModified
			: undefined;
		localStorage.setItem("faqs", JSON.stringify({
			vi: {
				time: __vieapps.faqs.vi.time,
				data: __vieapps.faqs.vi.data
			},
			en: {
				time: __vieapps.faqs.en.time,
				data: __vieapps.faqs.en.data
			}
		}));
	},
	fetch: function (callback) {
		__vieapps.faqs.vi.categories.forEach(categoryID => __vieapps.faqs.vi.fetchByCategory(categoryID, undefined, function () {
			__vieapps.faqs.store();
			if (typeof callback === "function") {
				callback();
			}
		}));
		__vieapps.faqs.en.categories.forEach(categoryID => __vieapps.faqs.en.fetchByCategory(categoryID, undefined, function () {
			__vieapps.faqs.store();
			if (typeof callback === "function") {
				callback();
			}
		}));
	},
	show: function (data, selector, categoryID, callback) {
		var html = "";
		data.filter(faq => faq.CategoryID == categoryID || faq.OtherCategories.indexOf(categoryID) > -1)
			.sortBy({ name: "PublishedTime", reverse: true }, { name: "LastModified", reverse: true })
			.take(7)
			.forEach(faq => {
				var url = (faq.URL || `/_permanentlink/${faq.RepositoryEntityID}/${faq.ID}`).replace("/", __vieapps.URLs.root);
				html += `<li class="item-list__li"><h3 class="item-list__title"><a href="${url}">${faq.Title}</a></h3></li>`;
			});
		$(selector).html(html);
		if (typeof callback === "function") {
			callback();
		}
	},
	init: function (callback) {
		var faqs = JSON.parse(localStorage.getItem("faqs") || "{\"vi\":{},\"en\":{}}");
		__vieapps.faqs.vi.time = !!faqs.vi.time ? new Date(faqs.vi.time) : undefined;
		__vieapps.faqs.vi.data = __vieapps.faqs.map(faqs.vi.data).sortBy({ name: "PublishedTime", reverse: true }, { name: "LastModified", reverse: true });
		if (!!__vieapps.faqs.vi.time) {
			setTimeout(function () {
				var filter = { Or: [] };
				__vieapps.faqs.vi.categories.forEach(categoryID => filter.Or.push({
					CategoryID: {
						Equals: categoryID
					}
				}));
				__vieapps.faqs.vi.fetch(
					function (data) {
						if (data.Objects.length && __timeDiff(__vieapps.faqs.vi.time, data.Objects.first().PublishedTime) > 0) {
							__vieapps.faqs.fetch(callback);
						}
					},
					filter,
					{
						LastModified: "Descending"
					},
					{
						TotalRecords: -1,
						TotalPages: 0,
						PageSize: 1,
						PageNumber: 0
					}
				);
			}, 2345);
		}
		else {
			__vieapps.faqs.fetch(callback);
		}
		__vieapps.faqs.en.time = !!faqs.en.time ? new Date(faqs.en.time) : undefined;
		__vieapps.faqs.en.data = __vieapps.faqs.map(faqs.en.data).sortBy({ name: "PublishedTime", reverse: true }, { name: "LastModified", reverse: true });
		if (!!__vieapps.faqs.en.time) {
			setTimeout(function () {
				var filter = { Or: [] };
				__vieapps.faqs.en.categories.forEach(categoryID => filter.Or.push({
					CategoryID: {
						Equals: categoryID
					}
				}));
				__vieapps.faqs.en.fetch(
					function (data) {
						if (data.Objects.length && __timeDiff(__vieapps.faqs.en.time, data.Objects.first().PublishedTime) > 0) {
							__vieapps.faqs.fetch(callback);
						}
					},
					filter,
					{
						LastModified: "Descending"
					},
					{
						TotalRecords: -1,
						TotalPages: 0,
						PageSize: 1,
						PageNumber: 0
					}
				);
			}, 2345);
		}
		else {
			__vieapps.faqs.fetch(callback);
		}
	}
};
$(function () {
	__vieapps.faqs.init();
});

;__vieapps.resources = {
	vi: {
		time: undefined,
		data: [],
		fetch: function (callback, sortBy, pagination) {
			var request = {
				FilterBy: {
					And: [
						{
							SystemID: {
								Equals: "6783dc1271ff449e95b74a9520964169"
							}
						},
						{
							RepositoryID: {
								Equals: "a95451e23b474fe5886bfb7cf843f53c"
							}
						},
						{
							RepositoryEntityID: {
								Equals: "f9d940be48f942e98b02695f245fdedb"
							}
						},
						{
							Status: {
								Equals: "Published"
							}
						}
					]
				},
				SortBy: sortBy || { Created: "Ascending" },
				Pagination: pagination || {
					TotalRecords: -1,
					TotalPages: 0,
					PageSize: 100,
					PageNumber: 0
				}
			};
			__vieapps.apis.fetch("portals", "cms.item", "search", undefined, { "x-request": __vieapps.crypto.jsonEncode(request), "ShowAttachments": "x" }, function (data) {
				__vieapps.resources.vi.data = __vieapps.resources.vi.data.concat(__vieapps.resources.map(data.Objects))
					.distinct((value, index, array) => array.findIndex(val => val.ID == value.ID) == index)
					.sortBy({ name: "Created", reverse: true });
				if (typeof callback === "function") {
					callback(data);
				}
			});
		},
		fetchAll: function (pagination, callback, stepCallback) {
			__vieapps.resources.vi.fetch(
				function (data) {
					if (typeof stepCallback === "function") {
						stepCallback(data);
					}
					pagination = data.Pagination;
					pagination.PageNumber++;
					if (pagination.PageNumber <= pagination.TotalPages) {
						setTimeout(function () {
							__vieapps.resources.vi.fetchAll(pagination, callback, stepCallback);
						}, 13);
					}
					else {
						__vieapps.resources.store();
						if (typeof callback === "function") {
							callback(data);
						}
					}
				},
				undefined,
				pagination
			);
		},
		show: function (listSelector, paginationSelector, page, callback) {
			page = page != undefined && +page > 0 ? +page : 1;
			if (!__vieapps.paginator.handlers["resources"]) {
				__vieapps.paginator.handlers["resources"] = function (pageNumber) {
					__vieapps.resources.vi.show(listSelector, paginationSelector, pageNumber);
				};
			}
			__vieapps.resources.show(listSelector, paginationSelector, __vieapps.resources.vi.data, page, callback);
		}
	},
	en: {
		time: undefined,
		data: [],
		fetch: function (callback, sortBy, pagination) {
			var request = {
				FilterBy: {
					And: [
						{
							SystemID: {
								Equals: "6783dc1271ff449e95b74a9520964169"
							}
						},
						{
							RepositoryID: {
								Equals: "a95451e23b474fe5886bfb7cf843f53c"
							}
						},
						{
							RepositoryEntityID: {
								Equals: "f9d940be48f942e98b02695f245fdedb"
							}
						},
						{
							Status: {
								Equals: "Published"
							}
						}
					]
				},
				SortBy: sortBy || { Created: "Ascending" },
				Pagination: pagination || {
					TotalRecords: -1,
					TotalPages: 0,
					PageSize: 100,
					PageNumber: 0
				}
			};
			__vieapps.apis.fetch("portals", "cms.item", "search", undefined, { "x-request": __vieapps.crypto.jsonEncode(request), "ShowAttachments": "x" }, function (data) {
				__vieapps.resources.en.data = __vieapps.resources.en.data.concat(__vieapps.resources.map(data.Objects))
					.distinct((value, index, array) => array.findIndex(val => val.ID == value.ID) == index)
					.sortBy({ name: "Created", reverse: true });
				if (typeof callback === "function") {
					callback(data);
				}
			});
		},
		fetchAll: function (pagination, callback, stepCallback) {
			__vieapps.resources.en.fetch(
				function (data) {
					if (typeof stepCallback === "function") {
						stepCallback(data);
					}
					pagination = data.Pagination;
					pagination.PageNumber++;
					if (pagination.PageNumber <= pagination.TotalPages) {
						setTimeout(function () {
							__vieapps.resources.en.fetchAll(pagination, callback, stepCallback);
						}, 13);
					}
					else {
						__vieapps.resources.store();
						if (typeof callback === "function") {
							callback(data);
						}
					}
				},
				undefined,
				pagination
			);
		},
		show: function (listSelector, paginationSelector, page, callback) {
			page = page != undefined && +page > 0 ? +page : 1;
			if (!__vieapps.paginator.handlers["resources"]) {
				__vieapps.paginator.handlers["resources"] = function (pageNumber) {
					__vieapps.resources.en.show(listSelector, paginationSelector, pageNumber);
				};
			}
			__vieapps.resources.show(listSelector, paginationSelector, __vieapps.resources.en.data, page, callback);
		}
	},
	store: function () {
		__vieapps.resources.vi.time = __vieapps.resources.vi.data.length
			? __vieapps.resources.vi.data.sortBy({ name: "LastModified", reverse: true }).first().LastModified
			: undefined;
		__vieapps.resources.en.time = __vieapps.resources.en.data.length
			? __vieapps.resources.en.data.sortBy({ name: "LastModified", reverse: true }).first().LastModified
			: undefined
		localStorage.setItem("resources", JSON.stringify({
			vi: {
				time: __vieapps.resources.vi.time,
				data: __vieapps.resources.vi.data.sortBy({ name: "Created", reverse: true })
			},
			en: {
				time: __vieapps.resources.en.time,
				data: __vieapps.resources.en.data.sortBy({ name: "Created", reverse: true })
			}
		}));
	},
	map: function (items) {
		return (items || []).map(item => {
			var url = item.Attachments && item.Attachments.length
				? item.Attachments.first().URIs.Direct
				: item.URL || __vieapps.URLs.portals;
			return {
				ID: item.ID,
				Title: item.Title,
				URL: url,
				Created: new Date(item.Created),
				LastModified: new Date(item.LastModified)
			};
		});
	},
	show: function (listSelector, paginationSelector, resources, page, callback) {
		var size = 7;
		var html = "";
		resources.sortBy({ name: "Created", reverse: true })
			.take(size, (page - 1) * size)
			.forEach(resource => html += `
			<div class="f-doc">
				<div class="f-doc__inner">
					<h3 class="f-doc__title"><a href="${resource.URL}" target="_blank">${resource.Title}</a></h3>
					<a href="${resource.URL}" target="_blank" class="f-doc__btn">
						<span>Download</span>
						<svg xmlns="http://www.w3.org/2000/svg" width="10.5" height="10.5" viewBox="0 0 10.5 10.5">
							<path id="Shape" d="M0,10V9.1H10V10ZM1.535,4.738,2.172,4.1,4.549,6.478V0h.9V6.478L7.828,4.1l.637.637L5,8.2Z" transform="translate(0.25 0.25)" fill="#0A54A8" stroke="#0A54A8" stroke-miterlimit="10" stroke-width="0.5"></path>
						</svg>
					</a>
				</div>
			</div>`);
		$(listSelector).html(html);
		__vieapps.paginator.show(paginationSelector, "resources", page, size, resources.length);
		if (typeof callback === "function") {
			callback();
		}
	},
	init: function (callback, stepCallback) {
		var resources = JSON.parse(localStorage.getItem("resources") || "{\"vi\":{},\"en\":{}}");
		__vieapps.resources.vi.time = resources.vi.time ? new Date(resources.vi.time) : undefined;
		__vieapps.resources.vi.data = __vieapps.resources.map(resources.vi.data).sortBy({ name: "Created", reverse: true });
		if (__vieapps.resources.vi.time !== undefined) {
			setTimeout(function () {
				__vieapps.resources.vi.fetch(
					function (data) {
						if (data.Objects.length && __timeDiff(__vieapps.resources.vi.time, data.Objects.first().LastModified) > 0) {
							__vieapps.resources.vi.data = [];
							__vieapps.resources.vi.fetchAll(undefined, callback, stepCallback);
						}
					},
					{
						LastModified: "Descending"
					},
					{
						TotalRecords: -1,
						TotalPages: 0,
						PageSize: 1,
						PageNumber: 0
					}
				);
			}, 2345);
		}
		else {
			__vieapps.resources.vi.fetchAll(undefined, callback, stepCallback);
		}
	}
};
$(function () {
	__vieapps.resources.init();
});

;__vieapps.stations = {
	time: undefined,
	data: [],
	fetch: function (callback, sortBy, pagination) {
		var request = {
			FilterBy: {
				And: [
					{
						SystemID: {
							Equals: "6783dc1271ff449e95b74a9520964169"
						}
					},
					{
						RepositoryID: {
							Equals: "a95451e23b474fe5886bfb7cf843f53c"
						}
					},
					{
						RepositoryEntityID: {
							Equals: "fc001e95204947538c944d3e8195d2dd"
						}
					},
					{
						Status: {
							Equals: "Published"
						}
					}
				]
			},
			SortBy: sortBy || { Created: "Ascending" },
			Pagination: pagination || {
				TotalRecords: -1,
				TotalPages: 0,
				PageSize: 50,
				PageNumber: 0
			}
		};
		__fetchAPIs("portals", "cms.item", "search", undefined, { "x-request": __jsonToBase64Url(request), }, function (data) {
			__vieapps.stations.data = __vieapps.stations.data.concat(data.Objects.map(station => {
				var position = station.GPSLocation && station.GPSLocation.trim() !== "" ? station.GPSLocation.trim().split(",").map(item => item.trim()) : ["", ""];
				var goods = station.Goods && station.Goods !== ""
					? station.Goods.indexOf("#") > -1
						? station.Goods.split("#").filter(item => item.trim() != "").map(item => item.trim())
						: station.Goods.indexOf(",") > -1
							? station.Goods.split(",").filter(item => item.trim() != "").map(item => item.trim())
							: [station.Goods.trim()]
					: undefined;
				var services = station.Services && station.Services !== ""
					? station.Services.indexOf("#") > -1
						? station.Services.split("#").filter(item => item.trim() != "").map(item => item.trim())
						: station.Services.indexOf(",") > -1
							? station.Services.split(",").filter(item => item.trim() != "").map(item => item.trim())
							: [station.Services.trim()]
					: undefined;
				var cardAccepts = station.CardAccepts && station.CardAccepts !== ""
					? station.CardAccepts.indexOf("#") > -1
						? station.CardAccepts.split("#").filter(item => item.trim() != "").map(item => item.trim())
						: station.CardAccepts.indexOf(",") > -1
							? station.CardAccepts.split(",").filter(item => item.trim() != "").map(item => item.trim())
							: [station.CardAccepts.trim()]
					: undefined;
				return {
					ID: station.ID,
					Title: station.Title,
					OwnedBy: station.OwnedBy,
					LastModified: new Date(station.LastModified),
					Province: station.Province && station.Province !== "" ? station.Province.trim() : undefined,
					MapInfo: {
						Position: {
							Latitude: position.length > 0 && position[0] != "" ? +position[0] : undefined,
							Longitude: position.length > 1 && position[1] != "" ? +position[1] : undefined
						},
						Marker: undefined,
						Box: undefined
					},
					ContactInfo: {
						Address: station.Address && station.Address !== "" ? station.Address.trim() : undefined,
						County: station.County && station.County !== "" ? station.County.trim() : undefined,
						District: station.District && station.District !== "" ? station.District.trim() : undefined,
						Province: station.Province && station.Province !== "" ? station.Province.trim() : undefined,
						Country: station.Country && station.Country !== "" ? station.Country.trim() : undefined,
						Email: station.Email && station.Email !== "" ? station.Email.trim().toLowerCase() : undefined,
						Phone: station.Phone && station.Phone !== "" ? station.Phone.trim() : undefined,
						Leader: {
							Name: station.LeaderName && station.LeaderName !== "" ? station.LeaderName.trim() : undefined,
							Mobile: station.LeaderMobile && station.LeaderMobile !== "" ? station.LeaderMobile.trim() : undefined
						}
					},
					StationInfo: {
						WorkingTimes: station.WorkingTimes && station.WorkingTimes !== "" ? station.WorkingTimes.trim() : "24/7",
						Goods: goods,
						Services: services,
						CardAccepts: cardAccepts,
						PumpsForAutos: !!station.PumpsForAutos,
						SelfService: !!station.SelftService,
						OilDispenser: +station.OilDispenser,
						StorageCapacity: +station.StorageCapacity
					}
				};
			})).distinct((value, index, array) => array.findIndex(val => val.ID == value.ID) == index).sortBy("Province", "Title");
			if (typeof callback === "function") {
				callback(data);
			}
		});
	},
	fetchAll: function (pagination, callback, stepCallback) {
		__vieapps.stations.fetch(
			function (data) {
				if (typeof stepCallback === "function") {
					stepCallback(data);
				}
				pagination = data.Pagination;
				pagination.PageNumber++;
				if (pagination.PageNumber <= pagination.TotalPages) {
					setTimeout(function () {
						__vieapps.stations.fetchAll(pagination, callback, stepCallback);
					}, 13);
				}
				else {
					__vieapps.stations.store();
					if (typeof callback === "function") {
						callback(data);
					}
				}
			},
			undefined,
			pagination
		);
	},
	store: function (callback) {
		__vieapps.stations.time = __vieapps.stations.data.length
			? __vieapps.stations.data.sortBy({ name: "LastModified", reverse: true }).first().LastModified
			: undefined;
		__vieapps.stations.data = __vieapps.stations.data.sortBy("Province", "Title");
		localStorage.setItem("stations", JSON.stringify({
			time: __vieapps.stations.time,
			data: __vieapps.stations.data.map(station => {
				return {
					ID: station.ID,
					Title: station.Title,
					OwnedBy: station.OwnedBy,
					LastModified: station.LastModified,
					Province: station.Province,
					MapInfo: {
						Position: station.MapInfo.Position,
						Marker: undefined,
						Box: undefined
					},
					ContactInfo: station.ContactInfo,
					StationInfo: station.StationInfo
				};
			})
		}));
		if (typeof callback === "function") {
			callback();
		}
	},
	init: function (callback, stepCallback) {
		var stations = JSON.parse(localStorage.getItem("stations") || "{}");
		__vieapps.stations.time = stations.time ? new Date(stations.time) : undefined;
		__vieapps.stations.data = (stations.data || []).sortBy("Province", "Title");
		if (__vieapps.stations.time !== undefined) {
			__vieapps.stations.data.forEach(station => station.LastModified = new Date(station.LastModified));
			setTimeout(function () {
				__vieapps.stations.fetch(
					function (data) {
						if (data.Objects.length && __timeDiff(__vieapps.stations.time, data.Objects.first().LastModified) > 0) {
							__vieapps.stations.data = [];
							__vieapps.stations.fetchAll(undefined, callback, stepCallback);
						}
						else if (typeof callback === "function") {
							callback();
						}
					},
					{
						LastModified: "Descending"
					},
					{
						TotalRecords: -1,
						TotalPages: 0,
						PageSize: 1,
						PageNumber: 0
					}
				);
			}, 2345);
		}
		else {
			__vieapps.stations.fetchAll(undefined, callback, stepCallback);
		}
	}
};
$(function () {
	__vieapps.stations.init();
});

;/* paginators */
__vieapps.paginator.template = {
	container: "<div class=\"{{css}}\"><ul>{{previous}}{{pages}}{{next}}</ul></div>",
	previous: "<li>{{anchor}}</li>",
	next: "<li>{{anchor}}</li>",
	pages: {
		container: undefined,
		page: "<li>{{anchor}}</li>",
		current: "<li class=\"current\">{{anchor}}</li>"
	}
};
__vieapps.paginator.css = {
	container: "pagination",
	previous: "btn-prev",
	next: "btn-next"
};
__vieapps.paginator.previous = {
	label: "",
	icon: "<i class=\"fa fa-angle-left\"></i>"
};
__vieapps.paginator.next = {
	label: "",
	icon: "<i class=\"fa fa-angle-right\"></i>"
};

/* languages */
var findCurrentLanguageSwitcher = function () {
	var current = __vieapps.language.split("-").first().toLowerCase() + ".html";
	var elements = $(".select-language .f-content > li").children();
	for (var index = 0; index < elements.length; index++) {
		var element = $(elements[index]);
		var href = element.attr("href");
		if (href.endsWith(current)) {
			return href;
		}
	}
	elements = $(".select-language .f-content > li.current").children();
	return elements.length ? $(elements[0]).attr("href") : undefined;
};

var prepareLanguageSwitchers = function () {
	var current = findCurrentLanguageSwitcher();
	if (!!current) {
		var src = `${__vieapps.URLs.portals}/_themes/sunrise/img/icon-vn.png`;
		$(".select-language").each(function () {
			var switcher = $(this);
			switcher.children("ul").children().each(function () {
				var element = $(this)
				var anchor = element.children().first();
				if (anchor.attr("href").endsWith(current)) {
					element.addClass("current");
					src = anchor.children().first().attr("src");
				}
				else {
					element.removeClass("current");
				}
			});
			switcher.children("p").first().children("span").first().children().first().attr("src", src);
		});
	}
};

var prepareLanguageResources = function () {
	var closeCtrl = $(".searchbox .item__header .item__close > span");
	var titleCtrl = $(".searchbox .title .title__title");
	var textCtrl = $(".searchbox .title .title__text");
	var keywordsCtrl = $("#search-keywords");
	var tagsCtrl = $(".searchbox .item__keyword .tag-list");
	if (__vieapps.language != "vi-VN") {
		console.log("Search", closeCtrl, titleCtrl, textCtrl, keywordsCtrl, tagsCtrl, __vieapps);
	}
};

/* hacks */
var moveElement = function (source, destination, insertAfter) {
	var from = $(source);
	var to = $(destination);
	if (from.length && to.length) {
		from.remove();
		if (!!insertAfter) {
			from.insertAfter(to);
		}
		else {
			from.insertBefore(to);
		}
	}
};

var moveElementOnContentSection = function (selector, insertAfter) {
	moveElement(selector, "div.page-content > .section.content", insertAfter);
};

var moveTitleElement = function (selector) {
	moveElementOnContentSection(selector);
};

$(function () {
	if ($("div.desktop.cms-content.view").length) {
		var content = $("div.page-content > .section.content");
		content.removeClass("sec-blogCategory pt-0");
		content.addClass("sec-blogDetail style2");
		$("div.page-content > .section.content .row.content").addClass("blogDetail__content");
		$("div.page-content > .section.content .row.content > .col-md-7").removeClass("col-lg-8");
		$("div.page-content > .section.content .row.content > .col-md-5").addClass("offset-lg-1");
	}
	prepareLanguageSwitchers();
	prepareLanguageResources();
});

