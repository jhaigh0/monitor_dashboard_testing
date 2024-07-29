import argparse
from collections import defaultdict
from dataclasses import astuple, dataclass
from jinja2 import FileSystemLoader, Environment
from typing import Dict, List
from datetime import datetime
import logging
import sys

from database_handler import DatabaseHandler
logger = logging.getLogger("update site")
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


@dataclass
class ResultInfo:
    job_name: str
    build_number: str
    os: str
    result: str
    finish_time: str

    def __iter__(self):
        return iter(astuple(self))


def main():
    args = parse_args()
    results = get_test_results(args.database_path)
    format_templates(results)


def get_test_results(db_path: str):
    db_handler = DatabaseHandler(db_path)
    results = db_handler.get_all_test_results()
    logger.info(f"Retrieved {len(results)} test results")
    results_per_test = defaultdict(list)
    for job_name, build_number, test_name, os, result, finish_time in results:
        info = ResultInfo(job_name, build_number, os, result, finish_time)
        results_per_test[test_name].append(info)

    return results_per_test


def format_templates(test_results):
    environment = Environment(loader=FileSystemLoader('web/templates/'))
    table_template = environment.get_template('os_table.html.j2')
    for os in {'Linux', 'Windows', 'MacOS'}:
        rows = create_table_rows(test_results, os)
        context = {"os_name": os, "rows_data": rows}
        with open(f"web/html/{os}_table.html", "w") as fp:
            fp.write(table_template.render(context))
            logger.info(f"Wrote to {fp.name}")


def create_table_rows(test_results: Dict[str, List[ResultInfo]], os: str):
    rows = []
    for test_name, results in test_results.items():
        filtered_results = [result for result in results if result.os == os]
        if filtered_results:
            filtered_results.sort(key=lambda result: int(result.finish_time))
            rows.append([test_name, len(filtered_results),
                         datetime.fromtimestamp(int(filtered_results[-1].finish_time) / 1000).strftime("%y-%m-%d")])
    return rows


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-db', '--database_path', type=str, help="path to the test results database")
    return parser.parse_args()


if __name__ == '__main__':
    main()
