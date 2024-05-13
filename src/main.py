import datetime
import os

from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.oauth2 import service_account

load_dotenv()
KEY_DIR = os.environ['KEY_DIR']
credentials = service_account.Credentials.from_service_account_file(
    os.path.join(KEY_DIR, 'KEY.json')
)
client = BetaAnalyticsDataClient(credentials=credentials)

dimensions = [Dimension(name='pagePath'), Dimension(name='pageTitle')]
metrics = [Metric(name='screenPageViews')]
RESOURCE_ID = os.environ['RESOURCE_ID']
request = RunReportRequest(
    property=f'properties/{RESOURCE_ID}',
    date_ranges=[DateRange(start_date='28daysAgo', end_date='today')],
    dimensions=dimensions,
    metrics=metrics,
    limit=15,
)
response = client.run_report(request)

EXPORT_DIR = os.environ['EXPORT_DIR']
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
    }
    for row in response.rows:
        if row.dimension_values[0].value in ignored_paths:
            continue
        f.write(
            f'{rank}. [{row.dimension_values[1].value[:-14]}]({row.dimension_values[0].value})\n'
        )
        rank += 1
        if rank > 10:
            break

    f.write(f'\n每日更新。最近更新時間：`{datetime.datetime.now().strftime("%Y/%m/%d %H:%M")}`\n')
