import csv
import datetime
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account

from src.functions import _write_top_pages, filter_and_format_page_views, get_raw_page_views

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
credentials = service_account.Credentials.from_service_account_file(
    os.path.join(os.environ['KEY_PATH']),
)
client = BetaAnalyticsDataClient(credentials=credentials)


def get_processed_page_views(client, start_date, end_date, limit) -> list[tuple]:
    """
    Retrieves and formats page views data from the Google Analytics API.

    Args:
        client (GoogleAnalyticsClient): The client object used to make API requests.
        start_date (str): The start date of the date range for the report.
        end_date (str): The end date of the date range for the report.
        limit (int): The maximum number of results to return.

    Returns:
        list[tuple]: A list of tuples containing the formatted data.

    example:
    [
        ('/path/to/page/1/', 'Page Title 1', 300),
        ('/path/to/page/2/', 'Page Title 2', 200),
        ('/path/to/page/3/', 'Page Title 3', 100),
    ]
    """
    raw_page_views = get_raw_page_views(
        client=client, start_date=start_date, end_date=end_date, limit=limit
    )
    return filter_and_format_page_views(page_views=raw_page_views)


def export_page_views_to_markdown(page_views) -> None:
    """
    Export page views to a Markdown file.

    Args:
        formatted_page_views: A list of tuples containing the formatted data.
            example: [('/path/to/page/', 'Page Title', 100), ...]
        ignored_paths: A list of paths to be ignored.
    """
    EXPORT_DIR = os.environ['EXPORT_DIR']
    export_path = os.path.join(EXPORT_DIR, 'index.md')
    with open(export_path, 'w') as f:
        f.write('---\n')
        f.write('title: 本站熱門文章排名\n')
        f.write('layout: page\n')
        f.write('comments: false\n')
        f.write('permalink: /ranking/\n')
        f.write('---\n')
        f.write('# 本站熱門文章排名\n\n')
        f.write('排名依據：**最近 28 天瀏覽數**\n')
        f.write('### 瀏覽前 10 名\n\n')

        _write_top_pages(page_views=page_views, f=f, limit=10)


def _views_to_dict(page_views: list[tuple]) -> dict:
    """
    Convert page views to a dictionary. Ignore duplicate paths.

    Args:
        page_views (list[tuple]): A list of tuples containing the formatted data.
            example: [('/path/to/page/', 'Page Title', 100), ...]

    Returns:
        dict: A dictionary containing the page views.
    """
    views_dict = {}
    for path, title, views in page_views:
        if path not in views_dict:
            views_dict[path] = (title, views)
    return views_dict


def get_top_rising_page(prev_views, recent_views, limit=10) -> list[tuple[str, str, str]]:
    """
    Get the top rising pages based on the percentage change in views.

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


def append_page_views_to_markdown(top_rising_pages) -> None:
    """
    Append top rising pages to a Markdown file.

    Args:
        top_rising_pages: A list of tuples containing the top rising pages.
            example: [('/path/to/page/', 'Page Title', '50.0%'), ...]
    """
    EXPORT_DIR = os.environ['EXPORT_DIR']
    export_path = os.path.join(EXPORT_DIR, 'index.md')
    with open(export_path, 'a') as f:
        f.write('\n### 上升前 10 名\n\n')
        for rank, (path, title, change) in enumerate(top_rising_pages, start=1):
            f.write(f'{rank}. [{title}]({path})（{change}）\n')

        f.write(
            f'\n最後更新時間：`{datetime.datetime.now().strftime("%Y/%m/%d %H:%M")}`'
            '（每日下午 3 點更新）\n'
        )


def export_page_views_to_csv(page_views, ignored_paths):
    """
    Export page views to a CSV file.

    Args:
        page_views: An object representing the page views.
        ignored_paths: A list of paths to be ignored.

    Returns:
        None
    """
    base_dir = Path(__file__).resolve().parent.parent
    export_dir = os.path.join(base_dir, 'data')
    export_path = os.path.join(export_dir, 'index.csv')
    with open(export_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'path', 'views', 'date'])

        rank = 1
        for row in page_views.rows:
            if row.dimension_values[0].value in ignored_paths:
                continue
            writer.writerow(
                [rank, row.dimension_values[1].value[:-14], row.dimension_values[0].value]
            )
            rank += 1
            if rank > 10:
                break


if __name__ == '__main__':
    # export_page_views_to_csv(recent_page_views, ignored_paths)
    # Write Top 10 pages to a Markdown file
    page_views = get_processed_page_views(
        client=client, start_date='28daysAgo', end_date='today', limit=15
    )
    export_page_views_to_markdown(page_views=page_views)

    # Append Top 10 rising pages to a Markdown file
    previous_page_views = get_processed_page_views(
        client=client, start_date='56daysAgo', end_date='28daysAgo', limit=200
    )
    recent_page_views = get_processed_page_views(
        client=client, start_date='28daysAgo', end_date='today', limit=200
    )

    top_10_rising_pages = get_top_rising_page(
        prev_views=previous_page_views, recent_views=recent_page_views
    )
    append_page_views_to_markdown(top_rising_pages=top_10_rising_pages)
    logger.info('Executing done.')
