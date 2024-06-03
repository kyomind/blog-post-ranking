import csv
import datetime
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account

from src.functions import _write_top_x_pages, format_page_views, get_raw_page_views

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
credentials = service_account.Credentials.from_service_account_file(
    os.path.join(os.environ['KEY_PATH']),
)
client = BetaAnalyticsDataClient(credentials=credentials)

ignored_paths = {
    '/',
    '/archives/',
    '/ranking/',
    '/tags/',
    '/categories/',
    '/series/',
    '/subscribe/',
    '/page/',
    '/django/',
}


def get_formatted_page_views(client, start_date, end_date, limit) -> list[tuple]:
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
    return format_page_views(page_views=raw_page_views)


def export_page_views_to_markdown(page_views, ignored_paths):
    """
    Export page views to a Markdown file.

    Args:
        formatted_page_views: A list of tuples containing the formatted data.
            example: [('/path/to/page/', 'Page Title', 100), ...]
        ignored_paths: A list of paths to be ignored.
    """
    EXPORT_DIR = os.environ.get('EXPORT_DIR')
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
        f.write('### 瀏覽數前 10 名\n\n')

        _write_top_x_pages(formatted_page_views=page_views, ignored_paths=ignored_paths, f=f, x=10)


def append_page_views_to_markdown(recent_page_views, previous_page_views, ignored_paths):
    """
    Append page views to an existing Markdown file.

    Args:
        recent_page_views: An object representing the recent page views.
        previous_page_views: An object representing the previous page views.
        ignored_paths: A list of paths to be ignored.

    Returns:
        None
    """
    EXPORT_DIR = os.environ.get('EXPORT_DIR')
    export_path = os.path.join(EXPORT_DIR, 'index.md')
    with open(export_path, 'a') as f:
        f.write('\n\n### 上升前 10 名\n')
        f.write('**近期更新**🐥\n')

        rank = 1
        for row in recent_page_views.rows:
            if row.dimension_values[0].value in ignored_paths:
                continue
            f.write(
                f'{rank}. [{row.dimension_values[1].value[:-14]}]'
                f'({row.dimension_values[0].value})\n'
            )
            rank += 1
            if rank > 10:
                break

        f.write('\n**前期更新**🐣\n')
        rank = 1
        for row in previous_page_views.rows:
            if row.dimension_values[0].value in ignored_paths:
                continue
            f.write(
                f'{rank}. [{row.dimension_values[1].value[:-14]}]'
                f'({row.dimension_values[0].value})\n'
            )
            rank += 1
            if rank > 10:
                break

        f.write(
            f'\n最後更新時間：`{datetime.datetime.now().strftime("%Y/%m/%d %H:%M")}`'
            '（每日下午 3 點更新）'
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
    page_views = get_formatted_page_views(
        client=client, start_date='28daysAgo', end_date='today', limit=15
    )
    # previous_page_views = get_page_views(
    #     client=client, start_date='56daysAgo', end_date='28daysAgo', limit=10
    # )
    export_page_views_to_markdown(page_views=page_views, ignored_paths=ignored_paths)
    logger.info('Executing done.')
