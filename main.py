# Add this import
from Tool import ToolDlg
from logging.config import dictConfig
import logging
logging.getLogger().addHandler(logging.StreamHandler())

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(message)s',
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'default',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
            'formatter': 'default',
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['file', 'file_error']
    }
})

logging.debug('프로그램 시작')

# UI
app = ToolDlg(None)
app.mainloop()