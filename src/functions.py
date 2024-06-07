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
        tuple: A tuple containing the formatted data.

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


def _write_top_pages(
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
        paths_with_rank (list): A list of tuples containing the path and rank.
    """
    for rank, (path, title, _) in enumerate(page_views, start=1):
        if path in path_ranks:
            yesterday_rank = path_ranks[path]
            if yesterday_rank > rank:  # 排名上升
                f.write(f'{rank}. [{title}]({path}) +{yesterday_rank - rank}\n')
            elif yesterday_rank == rank:  # 排名不變
                f.write(f'{rank}. [{title}]({path})\n')
            else:  # 排名下降
                f.write(f'{rank}. [{title}]({path}) ↓\n')
        else:
            f.write(f'{rank}. [{title}]({path}) new!\n')
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


def _write_views_to_csv(views_dict: dict, file_name='views') -> None:
    """
    Write the page views to a Markdown file.

    Args:
        views_dict (dict): A dictionary containing the page views.
            example: {'/path/to/page/': ('Page Title', 100), ...}
    """

    write_path = os.path.join(BASE_DIR, 'data', f'{file_name}.csv')
    with open(write_path, 'w') as f:
        f.write('title, views\n')
        for title, views in views_dict.values():
            f.write(f'{title}, {views}\n')


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
    _write_views_to_csv(prev_dict, file_name='prev_views')
    recent_dict = _views_to_dict(recent_views)

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
