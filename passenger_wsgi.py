import os
import sys

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(__file__))

def application(environ, start_response):
    """
    Simple WSGI application for cPanel.
    Since this is a Telegram Polling Bot, this web endpoint just checks availability.
    The actual bot should be run via cPanel Terminal or Cron Job.
    """
    status = '200 OK'
    output = b'Telegram AI Bot is deployed.\n\nPlease run "python main.py" in terminal to start the bot process.'

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
