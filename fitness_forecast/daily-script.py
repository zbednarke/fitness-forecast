from shutil import copyfile
import numpy as np
from pathlib import Path
import plotly
import plotly.graph_objects as go
import datetime


if __name__ == '__main__':
    # first move today;s downloaded file
    today = datetime.date.today()
    todaystr = today.strftime('%Y%m%d')
    filestr = 'fitbit_export_' + todaystr
    download_dir = '/Users/zacharybednarke/Downloads/'
    fname = Path.joinpath(download_dir, filestr)
    copyfile(src, dst)

# then parse file

# then update fitness history

# then plot interactively