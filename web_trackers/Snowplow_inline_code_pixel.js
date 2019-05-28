;document.addEventListener('DOMContentLoaded', init, false);

  function init() {
    adsBlocked(function (blocked) {
      if (blocked) {
        var hostUrl = window.location.href;
        var path = window.location.pathname;
        document.getElementById('result').innerHTML = "<div style=\"display: none; visibility: hidden;\"><img src=\"https://spm.gov.bc.ca/i?&e=pv&page=" + path + "&url=" + hostUrl +  "&aid=Snowplow_standalone_pixel&p=web&tv=1-0-0\" /></div>";
      } else {
        // <!-- Snowplow starts plowing - Standalone vA.2.10.2 -->
        (function(p,l,o,w,i,n,g){if(!p[i]){p.GlobalSnowplowNamespace=p.GlobalSnowplowNamespace||[];
        p.GlobalSnowplowNamespace.push(i);p[i]=function(){(p[i].q=p[i].q||[]).push(arguments)
        };p[i].q=p[i].q||[];n=l.createElement(o);g=l.getElementsByTagName(o)[0];n.async=1;
        n.src=w;g.parentNode.insertBefore(n,g)}}(window,document,"script","https://sp-js.apps.gov.bc.ca/MDWay3UqFnIiGVLIo7aoMi4xMC4y.js","snowplow"));

        var collector = drupalSettings['gdx_collector'];
        window.snowplow('newTracker','rt',collector, {
          appId: "Snowplow_standalone_nopixel",
          platform: 'web',
          post: true,
          forceSecureTracker: true,
          contexts: {
            webPage: true,
            performanceTiming: true
          }
        });
        window.snowplow('enableActivityTracking', 30, 30); // Ping every 30 seconds after 30 seconds
        window.snowplow('enableLinkClickTracking');
        window.snowplow('trackPageView');
        //  <!-- Snowplow stop plowing -->
      }
    })
  }

  function adsBlocked(callback) {
    var scriptURL = 'https://sp-js.apps.gov.bc.ca/MDWay3UqFnIiGVLIo7aoMi4xMC4y.js';

    var myInit = {
      method: 'HEAD',
      mode: 'no-cors'
    };

    var myRequest = new Request(scriptURL, myInit);

    fetch(myRequest).then(function (response) {
      return response;
    }).then(function (response) {
      // Tracking script blocked
      callback(false)
    }).catch(function (e) {
      // Tracking script not blocked
      callback(true)
    }); 
  }