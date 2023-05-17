from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (FavoriteRecipe, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Tag)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from users.models import Follow

from .filters import IngredientSearchFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (CheckFavoriteSerializer, CheckShoppingCartSerializer,
                          CheckSubscribeSerializer, FollowSerializer,
                          IngredientSerializer, RecipeAddingSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          TagSerializer)

User = get_user_model()
FILENAME = 'shopping_cart.txt'
HEADER_FILE_CART = 'Мой список покупок:\n\nНаименование - Кол-во/Ед.изм.\n'


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_class = IngredientSearchFilter


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @transaction.atomic()
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckFavoriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.add_object(FavoriteRecipe, request.user, pk)

    @favorite.mapping.delete
    def del_favorite(self, request, pk=None):
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckFavoriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.delete_object(FavoriteRecipe, request.user, pk)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckShoppingCartSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.add_object(ShoppingCart, request.user, pk)

    @shopping_cart.mapping.delete
    def del_shopping_cart(self, request, pk=None):
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckShoppingCartSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.delete_object(ShoppingCart, request.user, pk)

    def add_object(self, model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeAddingSerializer(recipe)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    def delete_object(self, model, user, pk):
        model.objects.filter(user=user, recipe__id=pk).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=['get'], detail=False, permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).order_by('ingredient__name').annotate(total=Sum('amount'))
        result = HEADER_FILE_CART
        result += '\n'.join([
            f'{ingredient["ingredient__name"]} - {ingredient["total"]}/'
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ])
        response = HttpResponse(result, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={FILENAME}'
        return response


class FollowViewSet(UserViewSet):
    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):

        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'author': author.id,
        }
        serializer = CheckSubscribeSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        result = Follow.objects.create(user=user, author=author)
        serializer = FollowSerializer(result, context={'request': request})
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'author': author.id,
        }
        serializer = CheckSubscribeSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user.follower.filter(author=author).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
