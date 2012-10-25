from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^dashboard', 'rapidsms.views.dashboard', name='rapidsms-dashboard'),

    (r'^account/', include('rapidsms.urls.login_logout')),
    (r'^broadcast/', include('broadcast.urls')),
    (r'^groups/', include('groups.urls')),
    (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
)
