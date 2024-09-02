from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class RecipePermission(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        if request.method in ('PATCH', 'DELETE'):
            return obj.author == request.user
        return request.method in SAFE_METHODS
