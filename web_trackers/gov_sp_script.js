// <!-- Snowplow starts plowing - CMS Lite vE.2.14.0 -->
    ;(function(p,l,o,w,i,n,g){if(!p[i]){p.GlobalSnowplowNamespace=p.GlobalSnowplowNamespace||[];
     p.GlobalSnowplowNamespace.push(i);p[i]=function(){(p[i].q=p[i].q||[]).push(arguments)
     };p[i].q=p[i].q||[];n=l.createElement(o);g=l.getElementsByTagName(o)[0];n.async=1;
     n.src=w;g.parentNode.insertBefore(n,g)}}(window,document,"script","https://www2.gov.bc.ca/StaticWebResources/static/sp/sp-2-14-0.js","snowplow"));
     var collector = 'spm.apps.gov.bc.ca';
     window.snowplow('newTracker','rt',collector, {
    	appId: "Snowplow_gov",
        cookieLifetime: 86400 * 548,
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
     //This checks if there is a current page id and if not just do the basic trackPageView
     if (document.querySelector("meta[name='current_page_id']")) {
        window.snowplow(
    	    'trackPageView',
    	    null,
    	    [{
                schema: 'iglu:ca.bc.gov/meta_data/jsonschema/1-0-0',
                data: {
                    node_id: document.querySelector("meta[name='current_page_id']").getAttribute("content")
                }
    	    }]
     );}
     else {
       window.snowplow('trackPageView');
     }

// <!-- Snowplow stops plowing -->
