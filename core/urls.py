from django.urls import include, path

urlpatterns = [
    path('', include('learning.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]