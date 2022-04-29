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

dashboard = SimpleRouter()
dashboard.register("dashboard/graph", DashboardViewSetAdmin.get_graph)
dashboard.register("dashboard/summary", DashboardViewSetAdmin.get_summary)
dashboard.register("dashboard/bts", DashboardViewSetAdmin.get_bts)
dashboard.register("dashboard/trading_users", DashboardViewSetAdmin.get_trading_users)
dashboard.register("dashboard/shares", DashboardViewSetAdmin.get_shares)
dashboard.register("dashboard/shares_value", DashboardViewSetAdmin.get_shares_value)
dashboard.register("dashboard/cars_with_shares", DashboardViewSetAdmin.get_cars_with_shares)
dashboard.register("dashboard/total_trading_cash", DashboardViewSetAdmin.get_total_trading_cash)
dashboard.register("dashboard/recent_trade_activities", DashboardViewSetAdmin.get_recent_trading_activities)




# urlpatterns = transactions_router_admin.urls
