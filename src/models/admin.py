from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from src.models.models import *


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            _('Personal info'),
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                )
            },
        ),
        (_('Profile asset'), {'fields': ('profile_picture',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

# admin.site.register(UserAdmin)
admin.site.register(LoginSessions)
admin.site.register(Otp)
admin.site.register(TransactionPin)
admin.site.register(CarMerchant)
admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(Banks)
admin.site.register(BankAccount)
admin.site.register(Car)
admin.site.register(SpareParts)
admin.site.register(MiscellaneousExpenses)
admin.site.register(CarMaintenance)
admin.site.register(Trade)
admin.site.register(TradeUnit)
admin.site.register(Disbursement)
admin.site.register(Activity)
admin.site.register(Assets)
admin.site.register(CarProduct)
admin.site.register(CarFeature)
admin.site.register(Notifications)
admin.site.register(VehicleInfo)
