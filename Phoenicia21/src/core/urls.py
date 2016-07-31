from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.main, name='main'),
    url(r'main$', views.main, name='main'),
    url(r'docs_add$', views.docs_add, name='docs_add'),
    url(r'docs_search$', views.docs_search, name='docs_search'),
    url(r'operations_view$', views.operations_view, name='operations_view'),
    url(r'operations_transfer$', views.operations_transfer, name='operations_transfer'),
    url(r'operations_bank$', views.operations_bank, name='operations_bank'),
    url(r'operations_many$', views.operations_many, name='operations_many'),
    url(r'auth_login$', views.auth_login, name='auth_login'),
    url(r'profile$', views.profile, name='profile'),
    url(r'acess_denied$', views.access_denied, name='access_denied'),
    url(r'auth_logout$', views.auth_logout, name='auth_logout'),
    url(r'admin_units$', views.admin_units, name='admin_units'),
    url(r'admin_users$', views.admin_users, name='admin_users'),
    url(r'admin_balance$', views.admin_balance, name='admin_balance'),
    url(r'admin_tags$', views.admin_tags, name='admin_tags'),
    url(r'admin_doctitle$', views.admin_doctitle, name='admin_doctitle'),
    url(r'admin_invoices$', views.admin_invoices, name='admin_invoices'),
    url(r'restore_password$', views.restore_password, name='restore_password'),
    url(r'reports_cash$', views.reports_cash, name='reports_cash'),
    url(r'reports_balance$', views.reports_balance, name='reports_balance'),
    url(r'invoices$', views.invoices, name='invoices'),
    url(r'invoices_upload$', views.invoices_upload, name='invoices_upload'),
]