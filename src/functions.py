"""
helper functions
"""

import os
from collections.abc import Iterable

from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, Row, RunReportRequest

IGNORED_PATHS = (
    '/',
    '/archives/',
    '/ranking/',
    '/tags/',
    '/categories/',
    '/series/',
    '/subscribe/',
    '/page/',
    '/django/',
)


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


def format_page_views(page_views: Iterable) -> list[tuple]:
    """
    Formats the page views data.
    1. Transforms the data into a list of tuples.
    2. Filters out ignored paths.

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
            row.metric_values[0].value,
        )
        for row in page_views
        if not row.dimension_values[0].value.startswith(IGNORED_PATHS)
    ]


def _write_top_x_pages(page_views: list, f, x=10) -> None:
    """
    Writes the top x pages to a file. Default is top 10.

    Args:
        formatted_page_views (list): A list of tuples containing page information.
        ignored_paths (list): A list of paths to be ignored.
        f (file): The file object to write the top pages to.
        x (int, optional): The number of top pages to write. Defaults to 10.
    """
    rank = 1
    for path, title, _ in page_views:
        f.write(f'{rank}. [{title}]({path})\n')
        rank += 1
        if rank > x:
            break
