import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import time
import json
import datetime


# =============================================================================
#                                   CONFIGS
# =============================================================================

load_dotenv()
COOKIES = {"MoodleSessionedisciplinas": os.getenv("MOODLE_SESSION")}
COURSE_ID = os.getenv("ID")
DELTA_TIME = int(os.getenv("DELTA_TIME"))
URL = f"https://edisciplinas.usp.br/user/index.php?page=0&perpage=5000&contextid=0&id={COURSE_ID}&newcourse"
if not os.path.exists("output"):
    os.makedirs("output")


# =============================================================================
#                                   MAIN
# =============================================================================

def main():
    it = 0
    while True:

        try:
            print(f"[INFO] Updating: Iteration {it}")
            update(it)
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            print(f"[ERROR] Could not update infos: {e}")
            raise e

        try:
            time.sleep(DELTA_TIME)
        except KeyboardInterrupt:
            return 0

        it += 1


# =============================================================================
#                                   HELPERS
# =============================================================================

def update(it):
    response = requests.get(URL, cookies=COOKIES)

    if response.status_code != 200:
        raise Exception(f"[ERROR] Status code {response.status_code} != 200")

    soup = BeautifulSoup(response.content, 'html5lib')
    participant_count = int(soup.find("p", attrs={"data-region": "participant-count"}).text.split()[0])
    table = soup.find("table", attrs={"id": "participants"})

    obj = get_new_obj(table, participant_count)
    save_as_json(obj, it)


def get_new_obj(table, participant_count):
    obj = []
    for participant in range(1, participant_count):
        name_tag = table.find("th", attrs = {"id": f"user-index-participants-117430_r{participant}_c1"})
        last_login_tag = table.find("td", attrs = {"id": f"user-index-participants-117430_r{participant}_c4"})
        if name_tag is not None:
            participant_name = name_tag.text[2:]
            last_login = last_login_tag.text
            seconds = string_time_to_seconds(last_login)
            obj.append({"name": participant_name, "last_login": seconds})
        else:
            raise Exception(f"[ERROR] Participant {participant} not found!")
    return obj


def save_as_json(obj, it):
    file_name = "output/moodle-polling-{date:%d-%m-%Y_%H-%M-%S}_{it}.json".format(date=datetime.datetime.now(), it=it)
    with open(file_name, "w") as outfile:
        json.dump(obj, outfile, indent=4, ensure_ascii=False)


def string_time_to_seconds(time: str) -> int:
    seconds = 0
    num = 0
    for piece in time.split():
        if piece.isnumeric():
            num = int(piece)
        else:
            if piece == "dias":
                seconds += num * 24 * 60 * 60
            elif piece == "horas":
                seconds += num * 60 * 60
            elif piece == "minutos":
                seconds += num * 60
            elif piece == "segundos":
                seconds += num
    return seconds


if __name__ == "__main__":
    try:
        main()
        exit(0)
    except Exception:
        exit(1)
