from rest_framework.routers import DefaultRouter, SimpleRouter


from src.carpadi_admin.views import (
    TransactionsViewSetAdmin,
    CarMerchantsViewSetAdmin,
    CarBrandSerializerViewSet,
    CarViewSet,
    WalletViewSetAdmin,
    TradeViewSetAdmin,
    DisbursementViewSetAdmin,
    ActivityViewSetAdmin,
    DashboardViewSetAdmin,
)

from src.models.views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register(r'merchants', CarMerchantsViewSetAdmin)
router.register(r'transactions', TransactionsViewSetAdmin)
router.register(r'car-brands', CarBrandSerializerViewSet)
router.register(r'cars', CarViewSet)
router.register(r'wallets', WalletViewSetAdmin)
router.register(r'trades', TradeViewSetAdmin)
router.register(r'disbursements', DisbursementViewSetAdmin)
router.register(r'activities', ActivityViewSetAdmin)

# admin dashboard
router.register(r'dashboard/bts', DashboardViewSetAdmin.get_bts, basename='dashboard-bts')
# router.register(r'dashboard/graph', DashboardViewSetAdmin.get_graph, basename='dashboard-graph')
# router.register(r'dashboard/summary', DashboardViewSetAdmin.get_summary, basename='dashboard-summary')
# router.register(r'dashboard/trading_users', DashboardViewSetAdmin.get_trading_users, basename='dashboard-trading_users')
# router.register(r'dashboard/shares', DashboardViewSetAdmin.get_shares, basename='dashboard-shares')
# router.register(r'dashboard/shares_value', DashboardViewSetAdmin.get_shares_value, basename='dashboard-shares_value')
# router.register(r'dashboard/cars_with_shares', DashboardViewSetAdmin.get_cars_with_shares, basename='dashboard-cars_with_shares')
# router.register(r'dashboard/total_trading_cash', DashboardViewSetAdmin.get_total_trading_cash, basename='dashboard-total_trading_cash')
# router.register(r'dashboard/recent_trade_activities', DashboardViewSetAdmin.get_recent_trading_activities, basename='dashboard-recent_trade_activities')




# urlpatterns = transactions_router_admin.urls
