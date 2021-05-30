from django.urls import path
from . import views

app_name = "stonks"

urlpatterns = [
    path('', views.homepage, name="homepage"),
    path('register', views.register, name="register"),
    path('login', views.login_request, name="login"),
    path('logout', views.logout_request, name="logout"),
    path('stock/<str:ticker>/<str:length>', views.stock, name='stock'),
    path('sell/<str:ticker>', views.sell_request, name="sellstock"),
    path('buy/<str:ticker>', views.buy_request, name="buystock"),
    path('account/<str:username>', views.account, name="account")
]
