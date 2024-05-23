import csv
import datetime
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.oauth2 import service_account

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
    '/top/',
    '/about/',
    '/tags/',
    '/categories/',
    '/series/',
    '/subscribe/',
    '/page/',
}


def get_page_views(client, start_date, end_date, limit):
    """
    Retrieves page views data from the Google Analytics API.

    Args:
        client (GoogleAnalyticsClient): The client object used to make API requests.
        start_date (str): The start date of the date range for the report.
        end_date (str): The end date of the date range for the report.
        limit (int): The maximum number of results to return.

    Returns:
        GoogleAnalyticsResponse: The response object containing the page views data.
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
    return response


def export_page_views_to_markdown(page_views, ignored_paths):
    """
    Export page views to a Markdown file.

    Args:
        page_views: The page views object containing the data.
        ignored_paths: A list of paths to be ignored.

    Returns:
        None
    """
    EXPORT_DIR = os.environ.get('EXPORT_DIR')
    export_path = os.path.join(EXPORT_DIR, 'index.md')
    with open(export_path, 'w') as f:
        f.write('---\n')
        f.write('title: 熱門文章\n')
        f.write('layout: page\n')
        f.write('comments: false\n')
        f.write('permalink: /top/\n')
        f.write('---\n')
        f.write('# 本站熱門文章 TOP 10\n\n')
        f.write('排名依據：**最近 28 天瀏覽數**\n\n')

        rank = 1
        for row in page_views.rows:
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
            f'\n每日更新。最近更新時間：`{datetime.datetime.now().strftime("%Y/%m/%d %H:%M")}`\n'
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
    recent_page_views = get_page_views(
        client=client, start_date='28daysAgo', end_date='today', limit=15
    )
    # previous_page_views = get_page_views(
    #     client=client, start_date='56daysAgo', end_date='28daysAgo', limit=10
    # )
    export_page_views_to_markdown(recent_page_views, ignored_paths)
    logger.info('Executing done.')
