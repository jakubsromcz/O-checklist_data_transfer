from django.urls import path

from . import views


urlpatterns = [  
    
    path('ochecklist/', views.OchecklistAPIView.as_view(), name='ochecklist'),

    ]



