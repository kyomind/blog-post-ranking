import datetime
import logging
import os

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account

from src.functions import (
    _write_top_pages,
    filter_and_format_page_views,
    find_top_trending_pages,
    get_raw_page_views,
)

LOGGER_FORMAT = '%(asctime)s [%(levelname)s] %(filename)s %(lineno)d - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOGGER_FORMAT)
logger = logging.getLogger(__name__)

load_dotenv()
credentials = service_account.Credentials.from_service_account_file(
    os.path.join(os.environ['KEY_PATH']),
)
client = BetaAnalyticsDataClient(credentials=credentials)


def get_processed_page_views(client, start_date, end_date, limit) -> list[tuple]:
    """
    Get the processed page views data.

    Args:
        client (GoogleAnalyticsClient): The client object used to make API requests.
        start_date (str): The start date of the date range for the report.
        end_date (str): The end date of the date range for the report.
        limit (int): The maximum number of results to return.

    Returns:
        list[tuple]: A list of tuples containing the processed data.

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


if __name__ == '__main__':
    # Write Top 10 pages to a Markdown file
    recent_page_views = get_processed_page_views(
        client=client, start_date='28daysAgo', end_date='today', limit=100
    )
    export_page_views_to_markdown(page_views=recent_page_views)

    # Append Top 10 trending pages to the Markdown file
    previous_page_views = get_processed_page_views(
        client=client, start_date='56daysAgo', end_date='28daysAgo', limit=100
    )
    top_10_trending_pages = find_top_trending_pages(
        prev_views=previous_page_views, recent_views=recent_page_views
    )
    append_page_views_to_markdown(top_rising_pages=top_10_trending_pages)
    logger.info('Executing done.')
