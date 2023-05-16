from django.core.exceptions import ValidationError
from django_filters.fields import MultipleChoiceField
from django_filters.rest_framework import CharFilter, FilterSet, filters
from django_filters.widgets import BooleanWidget
from recipes.models import Ingredient, Recipe


class TagsMultipleChoiceField(
        MultipleChoiceField):
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'],
                code='required'
            )
        for val in value:
            if val in self.choices and not self.valid_value(val):
                raise ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice',
                    params={'value': val},
                )


class IngredientSearchFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    author = filters.AllValuesMultipleFilter(
        field_name='author__id',
        label='Автор'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        widget=BooleanWidget(),
        label='В корзине.',
        method='get_is_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(
        widget=BooleanWidget(),
        label='В избранных.',
        method='get_is_favorited'
    )
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return Recipe.objects.filter(favorite__user=user)
        return Recipe.objects.all()

    def get_is_in_shopping_cart(self, value):
        user = self.request.user
        if value:
            return Recipe.objects.filter(shopping_cart__user=user)
        return Recipe.objects.all()
