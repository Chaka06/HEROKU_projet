from django.urls import path
from . import views

app_name = 'banking'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/<slug:bank_slug>/', views.bank_login_view, name='bank_login'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/edit/confirm/', views.edit_profile_confirm_view, name='edit_profile_confirm'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/password/', views.change_password_view, name='change_password'),
    path('settings/password/confirm/', views.change_password_confirm_view, name='change_password_confirm'),
    path('settings/language/', views.change_language_view, name='change_language'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('support/', views.support_chat_view, name='support_chat'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('transactions/<int:transaction_id>/', views.transaction_detail_view, name='transaction_detail'),
    path('transactions/<int:transaction_id>/confirm/', views.confirm_transaction_view, name='confirm_transaction'),
    path('transactions/<int:transaction_id>/reject/', views.reject_transaction_view, name='reject_transaction'),
    path('transactions/<int:transaction_id>/download/', views.download_receipt_view, name='download_receipt'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('transfer/internal/', views.internal_transfer_view, name='internal_transfer'),
    path('beneficiaries/', views.beneficiaries_view, name='beneficiaries'),
    path('beneficiaries/add/', views.add_beneficiary_view, name='add_beneficiary'),
    path('rib/', views.rib_view, name='rib'),
    path('rib/<int:account_id>/download/', views.download_rib_pdf, name='download_rib'),
]
