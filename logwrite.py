import os
import sys

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# GLOBAL PATHS
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


# Function to write to the log file a message and a timestamp in blue like this, example :
# 2016-01-01 00:00:00 : msg
def writeLog(msg: str) -> None:
    """
    Write the message in the log file

    Parameters
    ----------
    msg : str
        The log message to write
    """
    with open(LOG_FILE, 'a') as f:
        f.write(LOG_COLOR + str(datetime.now()) + END_FORMAT + msg + '\n')


# Format the error to a string to get the file, line and message without whole traceback
def formatError(e: Exception) -> str:
    """
    Format the error
    Creates a string from the error to get a summary of file,
    line number, error type and message

    Parameters
    ----------
    e : Exception
        The exception to format

    Returns
    -------
    str
        Formated exception message
    """
    try:
        file = str(sys.exc_info()[-1].tb_frame).rsplit("'")[1]
        return f"{file} on l.{format(sys.exc_info()[-1].tb_lineno)} --> {type(e).__name__}, {e}".strip()
    except Exception:
        return str(e)


# Function to write to the error file the error message and a timestamp in red like this, example :
# 2016-01-01 00:00:00 : msg
def writeError(msg: str) -> None:
    """
    Write the message in the error file

    Parameters
    ----------
    msg : str
        The error message to write
    """
    with open(ERROR_FILE, 'a') as f:
        f.write(ERROR_COLOR + str(datetime.now()) + END_FORMAT + msg + '\n')
