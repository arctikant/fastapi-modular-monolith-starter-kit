from app.core.api import ListParamsBuilder
from app.core.db import FilterParam, ListParams, SortParam


class TestListParamsBuilder:
    def test_call(self):
        builder = ListParamsBuilder()
        result = builder(
            sort='id:asc,name:desc',
            filters='name:john,status_id:[1,2,3]',
            page=5,
            per_page=17,
        )

        assert isinstance(result, ListParams)
        assert isinstance(result.sort, list) and len(result.sort) == 2
        assert isinstance(result.sort[0], SortParam)
        assert result.sort[0].field == 'id'
        assert result.sort[0].order == 'asc'
        assert result.sort[1].field == 'name'
        assert result.sort[1].order == 'desc'

        assert isinstance(result.filters, list) and len(result.filters) == 2
        assert isinstance(result.filters[0], FilterParam)
        assert result.filters[0].field == 'name'
        assert result.filters[0].value == 'john'
        assert result.filters[1].field == 'status_id'
        assert result.filters[1].value == [1, 2, 3]

        assert result.page == 5
        assert result.per_page == 17
