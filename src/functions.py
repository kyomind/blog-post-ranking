"""
helper functions
"""

import os
import pathlib
from collections.abc import Iterable

from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, Row, RunReportRequest

IGNORED_PATHS = (
    '/archives/',
    '/ranking/',
    '/tags/',
    '/categories/',
    '/series/',
    '/subscribe/',
    '/page/',
    '/django/',
    '/top/',
)

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


def get_raw_page_views(client, start_date, end_date, limit) -> Iterable[Row]:
    """
    Retrieves page views data from the Google Analytics API.

    Args:
        client (GoogleAnalyticsClient): The client object used to make API requests.
        start_date (str): The start date of the date range for the report.
        end_date (str): The end date of the date range for the report.
        limit (int): The maximum number of results to return.

    Returns:
        Iterable[Row]: An iterable containing the raw page views data.

    example: (simplified)
    [
        {
            "dimension_values": [
                {
                    "value": "/path/to/page/"
                },
                {
                    "value": "Page Title - Code and Me"
                }
            ],
            "metric_values": [
                {
                    "value": 100
                }
            ]
        },
        {...},
        {...}
    ]
    """
    dimensions = [Dimension(name='pagePath'), Dimension(name='pageTitle')]
    metrics = [Metric(name='screenPageViews')]
    RESOURCE_ID = os.environ['RESOURCE_ID']
    request = RunReportRequest(
        property=f'properties/{RESOURCE_ID}',
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=dimensions,
        metrics=metrics,
        limit=limit,
    )
    response = client.run_report(request)
    return response.rows


def filter_and_format_page_views(page_views: Iterable, threshold=50) -> list[tuple]:
    """
    Formats the page views data.
    1. Transforms the data into a list of tuples.
    2. Filters out ignored paths.
    3. Transforms views from str to int.
    4. Eliminates pages with views below the threshold.

    Args:
        page_views: An iterable containing the raw page views data.

    Returns:
        list[tuple]: A list of tuples containing the formatted data.

    example:
    [
        ('/path/to/page/1/', 'Page Title 1', 300),
        ('/path/to/page/2/', 'Page Title 2', 200),
        ('/path/to/page/3/', 'Page Title 3', 100),
    ]
    """
    return [
        (
            row.dimension_values[0].value,
            row.dimension_values[1].value[:-14],
            int(row.metric_values[0].value),
        )
        for row in page_views
        if row.dimension_values[0].value != '/'
        and not row.dimension_values[0].value.startswith(IGNORED_PATHS)
        and int(row.metric_values[0].value) > threshold
    ]


def _write_top_page_entries(
    page_views: list,
    f,
    path_ranks: dict[str, int],
    limit=10,
) -> None:
    """
    Write the top pages to a Markdown file.

    Args:
        page_views (list): A list of tuples containing page information.
        f (file): The file object to write the top pages to.
        limit (int): The number of top pages to write. Defaults to 10.
        path_ranks (dict): A dictionary containing the path and its rank.
    """
    for rank, (path, title, view_count) in enumerate(page_views, start=1):
        if path in path_ranks:
            yesterday_rank = path_ranks[path]
            if yesterday_rank > rank:  # 排名上升
                f.write(f'{rank}. [{title}]({path}) +{yesterday_rank - rank}（{view_count}）\n')
            elif yesterday_rank == rank:  # 排名不變
                f.write(f'{rank}. [{title}]({path})（{view_count}）\n')
            else:  # 排名下降
                f.write(f'{rank}. [{title}]({path}) ↓（{view_count}）\n')
        else:
            f.write(f'{rank}. [{title}]({path}) NEW❗️（{view_count}）\n')
        if rank == limit:
            break


def _views_to_dict(page_views: list[tuple]) -> dict:
    """
    Convert page views to a dictionary. Ignore duplicate paths.

    Args:
        page_views (list[tuple]): A list of tuples containing the formatted data.
            example: [('/path/to/page/', 'Page Title', 100), ...]

    Returns:
        dict: A dictionary containing the page views.

    example:
    {
        '/path/to/page/1/': ('Page Title 1', 100),
        '/path/to/page/2/': ('Page Title 2', 200),
        '/path/to/page/3/': ('Page Title 3', 300),
    }
    """
    views_dict = {}
    for path, title, views in page_views:
        if path not in views_dict:
            views_dict[path] = (title, views)
    return views_dict


def _write_views_to_csv(prev_views: dict, recent_views: dict, file_name: str = 'views') -> None:
    """
    Write the page views to a Markdown file.

    Args:
        prev_views (dict): A dictionary containing the previous period page views.
            example: {'/path/to/page/': ('Page Title', 100), ...}
        recent_views (dict): A dictionary containing the recent period page views.
            example: {'/path/to/page/': ('Page Title', 200), ...}
    """
    write_path = os.path.join(BASE_DIR, 'data', f'{file_name}.csv')
    with open(write_path, 'w') as f:
        f.write('title, prev_views, recent_views, change, percent_change\n')
        for path, (title, views) in prev_views.items():
            if path in recent_views:
                f.write(f'{title}, {views}, {recent_views[path][1]}, ')
                f.write(f'{recent_views[path][1] - views}, ')
                f.write(f'{((recent_views[path][1] - views) / views) * 100:.2f}%\n')


def find_top_trending_pages(prev_views, recent_views, limit=10) -> list[tuple[str, str, str]]:
    """
    Find the top rising pages based on the percentage change in views.

    Args:
        prev_views (list[tuple]): Previous period page views.
        recent_views (list[tuple]): Recent period page views.
        limit (int): Number of top rising pages to output. Defaults to 10.

    Returns:
        list[tuple]: A list of tuples containing the top rising pages.

    example:
    [
        ('/path/to/page/1/', 'Page Title 1', '50.0%'),
        ('/path/to/page/2/', 'Page Title 2', '25.0%'),
        ('/path/to/page/3/', 'Page Title 3', '10.0%'),
    ]
    """
    prev_dict = _views_to_dict(prev_views)
    recent_dict = _views_to_dict(recent_views)
    _write_views_to_csv(  # 歷史數據，供內部參考
        prev_views=prev_dict, recent_views=recent_dict, file_name='prev_and_recent'
    )

    rising_pages = []
    for path, (recent_title, recent_views) in recent_dict.items():
        if path in prev_dict:
            _, prev_views = prev_dict[path]
            percentage_change = (recent_views - prev_views) / prev_views
            # ex: ('/path/to/page/', 'Page Title', 0.5)
            if percentage_change > 0:  # 只取增加的
                rising_pages.append((path, recent_title, percentage_change))

    # 按百分比變化從多到少排序
    rising_pages.sort(key=lambda x: x[2], reverse=True)

    # 取前 limit 個並格式化百分比變化
    top_rising_pages = [
        (path, title, f'{change * 100:.1f}%') for path, title, change in rising_pages[:limit]
    ]

    return top_rising_pages
