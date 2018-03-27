from django.urls import include
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import login, logout
from chat.views import index
from project import settings

urlpatterns = [
                  path('', index),
                  path('accounts/login/', login),
                  path('accounts/logout/', logout),
                  path('admin/', admin.site.urls),
                  path('quiz/', include('quiz.urls')),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
