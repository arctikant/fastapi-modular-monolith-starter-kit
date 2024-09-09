import ast
import re

from fastapi import Query
from pydantic import ValidationError

from app.core.db import FilterParam, ListParams, SortOrder, SortParam


class ListParamsBuilder:
    def __init__(
        self,
        list_params: type[ListParams] = ListParams,
        sort_param: type[SortParam] = SortParam,
        filter_param: type[FilterParam] = FilterParam,
    ):
        self.list_params = list_params
        self.sort_param = sort_param
        self.filter_param = filter_param

    def __call__(
        self,
        sort: str | None = Query(None, description='Sort parameters (e.g., field1:asc,field2:desc)'),
        filters: str | None = Query(None, description='Filter parameters (e.g., field1:value1,field2:[value1,value2])'),
        page: int = Query(1, ge=1, description='Page number'),
        per_page: int = Query(10, ge=1, le=100, description='Items per page'),
    ) -> ListParams:
        return self.list_params(
            sort=self._build_sort(sort), filters=self._build_filters(filters), page=page, per_page=per_page
        )

    def _build_sort(self, value: str | None) -> list[SortParam] | None:
        if value is None:
            return None

        try:
            items = [item.strip() for item in value.split(',') if item.strip()]
        except Exception:
            raise ValidationError('invalid_format')

        return [
            self.sort_param(
                field=item.split(':')[0], order=SortOrder(item.split(':')[1]) if ':' in item else SortOrder.asc
            )
            if isinstance(item, str)
            else item
            for item in items
        ]

    def _build_filters(self, value: str | None) -> list[FilterParam] | None:
        if value is None:
            return None

        try:
            # Split by comma, but not within square brackets
            items = re.split(r',(?![^\[]*])', value)
            items = [item.strip() for item in items if item.strip()]
        except Exception:
            raise ValidationError('invalid_filter_format')

        return [self._parse_filter_item(item) for item in items]

    def _parse_filter_item(self, item: str) -> FilterParam:
        if ':' not in item:
            raise ValidationError('invalid_filter_field_format')

        field, value = item.split(':', 1)
        return self.filter_param(field=field, value=self._convert_filter_value(value))

    def _convert_filter_value(self, value: str) -> str | int | list:
        # Check if the value is a list (enclosed in square brackets)
        if value.startswith('[') and value.endswith(']'):
            try:
                list_value = ast.literal_eval(value)
                if not isinstance(list_value, list):
                    raise ValueError
                return [self._convert_single_value(v) for v in list_value]
            except Exception:
                raise ValidationError('invalid_filter_list_value_format')
        else:
            return self._convert_single_value(value)

    def _convert_single_value(self, value: str) -> str | int:
        try:
            return int(value)
        except ValueError:
            return value
