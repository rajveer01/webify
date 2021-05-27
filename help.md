**How to start a App**

1. Python manage.py startapp db_refresher
2. Add in installed apps in INSTALLED_APPS list webify --> settings.py
3. How to add, 'db_refresher.apps.DbRefresherConfig', from apps.py file in new app
4. put urls.py file from any other module
5. Add url Pattern in Webify --> urls
        path('db_refresher/', include('db_refresher.urls')),
6. creare views and assign urls

