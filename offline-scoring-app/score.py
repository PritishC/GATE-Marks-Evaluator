import argparse
import json

import requests
from bs4 import BeautifulSoup

from question import Question

"""
Example usage -:

python score.py --response <responseURL> --key <keyURL>
"""


def fetch_url(url):
    res = requests.get(url)
    res.raise_for_status()

    return res.content


def get_answer_key(answer_sheet):
    ans_key = {}
    soup = BeautifulSoup(answer_sheet, features="html.parser")
    table = soup.select("table", _class="waffle")[0]
    td_elements = table.find_all("td", {"class": "s0"})[3:]
    subject_ids = table.find_all("td", {"class": "s2"})

    for index, ele in enumerate(td_elements):
        # Even elements are question short IDs and odd elements are answer keys
        if index % 2 == 1:
            continue

        # Store the answer key and subject ID
        ans_key[ele.string] = [td_elements[index + 1].string.strip('"'),
            subject_ids[index // 2].string]

    return ans_key


def process_questions(response_sheet, answer_key):
    question_list = []
    soup = BeautifulSoup(response_sheet, features="html.parser")
    question_tables = soup.find_all(class_="questionPnlTbl")

    for table in question_tables:
        question = Question(table, answer_key)
        question_list.append(question.serialize())

    return question_list


parser = argparse.ArgumentParser(description='Offline Scorer')
parser.add_argument('--response', dest='response_url', required=True)
parser.add_argument('--key', dest='key_url', required=True)

args = parser.parse_args()

response_sheet = fetch_url(args.response_url)
answer_sheet = fetch_url(args.key_url)

answer_key = get_answer_key(answer_sheet)
question_list = process_questions(response_sheet, answer_key)

with open("questions.json", "w") as f:
    json.dump(question_list, f, indent=4)

print("Success!")
