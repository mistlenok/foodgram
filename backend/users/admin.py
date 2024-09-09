from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import Follow, User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'password',
                    'first_name', 'last_name', 'is_staff',
                    'recipes_count', 'followers_count')
    list_filter = ('is_staff', )
    empty_value_display = 'Не заполнено'
    list_editable = ('is_staff', 'password')
    search_fields = ('username', 'email')

    @admin.display(description='Количество рецептов')
    def recipes_count(self, request):
        return request.recipes.all().count()

    @admin.display(description='Количество подписчиков')
    def followers_count(self, request):
        return request.following.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
