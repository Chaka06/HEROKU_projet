from django.urls import path
from . import gateway_views

app_name = 'gateway'

urlpatterns = [
    # Page principale — formulaire public
    path('',                                   gateway_views.gateway_home,              name='home'),

    # Paiement
    path('pay/<int:order_id>/',                gateway_views.gateway_payment,           name='payment'),
    path('pay/<int:order_id>/success/',        gateway_views.gateway_payment_success,   name='payment_success'),
    path('pay/<int:order_id>/error/',          gateway_views.gateway_payment_error,     name='payment_error'),
    path('pay/<int:order_id>/retry/',          gateway_views.gateway_payment_retry,     name='payment_retry'),

    # Historique des commandes (lecture seule, pas d'auth)
    path('orders/',                            gateway_views.gateway_orders,            name='orders'),
    path('orders/<int:order_id>/',             gateway_views.gateway_order_detail,      name='order_detail'),

    # Webhook GeniusPay (csrf_exempt dans la vue)
    path('webhook/geniuspay/',                 gateway_views.gateway_webhook_geniuspay, name='webhook_geniuspay'),
]
