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


def get_page_views(client, start_date, end_date):
    dimensions = [Dimension(name='pagePath'), Dimension(name='pageTitle')]
    metrics = [Metric(name='screenPageViews')]
    RESOURCE_ID = os.environ['RESOURCE_ID']
    request = RunReportRequest(
        property=f'properties/{RESOURCE_ID}',
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=dimensions,
        metrics=metrics,
        limit=15,
    )
    response = client.run_report(request)
    return response


recent_page_views = get_page_views(client, '28daysAgo', 'today')
previous_page_views = get_page_views(client, '56daysAgo', '29daysAgo')

BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = os.environ.get('EXPORT_DIR') or os.path.join(BASE_DIR, 'data')
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
    for row in recent_page_views.rows:
        if row.dimension_values[0].value in ignored_paths:
            continue
        f.write(
            f'{rank}. [{row.dimension_values[1].value[:-14]}]({row.dimension_values[0].value})\n'
        )
        rank += 1
        if rank > 10:
            break

    f.write(f'\n每日更新。最近更新時間：`{datetime.datetime.now().strftime("%Y/%m/%d %H:%M")}`\n')
    logger.info('Executing done.')
