import requests
import os
import sys
import time
import json
import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv


# =============================================================================
#                           CONFIGS AND CONSTANTS
# =============================================================================

load_dotenv()
COOKIES = {"MoodleSessionedisciplinas": os.getenv("MOODLE_SESSION")}
COURSE_ID = os.getenv("ID")
DELTA_TIME = int(os.getenv("DELTA_TIME"))
URL = f"https://edisciplinas.usp.br/user/index.php?page=0&perpage=5000&contextid=0&id={COURSE_ID}&newcoue"
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_END = "\033[0m"
COLOR_BLUE = "\033[94m"


# =============================================================================
#                                   MAIN
# =============================================================================

def main():
    it = 0
    while True:
        try:
            print_info(f"Updating: Iteration {it}")
            update(it)
            time.sleep(DELTA_TIME)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print_sad(f"Could not update infos: {e}:\n{e.__class__}:\n{e.__traceback__.tb_frame}")
            raise e
        it += 1
    return it


# =============================================================================
#                            LOGIC IMPLEMENTATION
# =============================================================================

def update(it):
    if not hasattr(update, "last_obj"):
        update.last_obj = {}

    response = requests.get(URL, cookies=COOKIES)

    if response.status_code != 200:
        raise Exception(f"[ERROR] Status code {response.status_code} != 200")

    soup = BeautifulSoup(response.content, 'html5lib')
    participant_count = int(soup.find("p", attrs={"data-region": "participant-count"}).text.split()[0])
    table = soup.find("table", attrs={"id": "participants"})

    obj = get_new_obj(table, participant_count, update.last_obj)
    update.last_obj = obj.copy()
    save_as_json(obj, it)


def get_new_obj(table, participant_count, last_obj):
    obj = {}
    for participant in range(1, participant_count):
        name_tag = table.find("th", attrs = {"id": f"user-index-participants-117430_r{participant}_c1"})
        if name_tag.span is not None:
            name_tag.span.decompose()
        last_login_tag = table.find("td", attrs = {"id": f"user-index-participants-117430_r{participant}_c4"})
        if name_tag is not None:
            participant_name = name_tag.text
            last_login = string_time_to_seconds(last_login_tag.text)
            obj[participant_name] = get_participant_obj(participant_name, last_login, last_obj)
        else:
            raise Exception(f"[ERROR] Participant {participant} not found!")
    return obj


def get_participant_obj(name, last_login, last_obj):
    participant_obj = {}
    participant_obj["last_login"] = last_login
    if name in last_obj and last_obj[name]["last_login"] > last_login:
        print_happy(f"Participant {name} just logged in!")
        participant_obj["logged_in"] = True
    else:
        participant_obj["logged_in"] = False
    return participant_obj


# =============================================================================
#                                   HELPERS
# =============================================================================

def save_as_json(obj, it):
    file_name = OUTPUT_DIR + "/moodle-polling-{date:%d-%m-%Y_%H-%M-%S}_{it}.json".format(date=datetime.datetime.now(), it=it)
    with open(file_name, "w") as outfile:
        json.dump(obj, outfile, indent=4, ensure_ascii=False)


def string_time_to_seconds(time):
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


def print_info(message, *args, **kwargs):
    print(COLOR_BLUE + "[INFO] " + message + COLOR_END, *args, **kwargs, flush=True)


def print_sad(message, *args, **kwargs):
    print(COLOR_RED + "[SAD :(] " + message + COLOR_END, *args, **kwargs, flush=True, file=sys.stderr)


def print_happy(message, *args, **kwargs):
    print(COLOR_GREEN + "[HAPPY :D] " + message + COLOR_END, *args, **kwargs, flush=True)


if __name__ == "__main__":
    try:
        it = main()
        print_happy(f"Completed {it} iterations in {it * DELTA_TIME} seconds!")
        exit(0)
    except Exception:
        exit(1)
