import os
import sys

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

#GLOBAL PATHS
HOME_PATH = os.getenv("home")
LOGS_PATH = HOME_PATH + os.getenv("logs")
LOG_FILE = LOGS_PATH + "josixout.log"
ERROR_FILE = LOGS_PATH + "josixerr.log"

LOG_COLOR = '\033[94m'
ERROR_COLOR = '\033[91m'
END_FORMAT = '\033[0m : ' 


# Adjust the log to keep only the message and not the color format
def adjustLog(msg: str, isError: bool) -> str:
    if msg == "\n":
        return msg

    if isError:
        return msg.replace(ERROR_COLOR, "").replace(END_FORMAT, " : ")
    else:
        return msg.replace(LOG_COLOR, "").replace(END_FORMAT, " : ")

#write a function to write to the log file a msg in and a timestamp in blue like this, example : 2016-01-01 00:00:00 : msg
def writeLog(msg : str):
    with open(LOG_FILE, 'a') as f:
        f.write(LOG_COLOR + str(datetime.now()) + END_FORMAT + msg + '\n')

#format the error to a string to get the file, line and message without whole traceback
def formatError(e : Exception) -> str:
    file = str(sys.exc_info()[-1].tb_frame).rsplit("'")[1]
    return f"{file} on l.{format(sys.exc_info()[-1].tb_lineno)} --> {type(e).__name__}, {e}".strip()

#write a function to write to the error file a msg in red in and a timestamp like this, example : 2016-01-01 00:00:00 : msg
def writeError(msg : str):
    with open(ERROR_FILE, 'a') as f:
        f.write(ERROR_COLOR + str(datetime.now()) + END_FORMAT + msg + '\n')
