#!/usr/bin/env python
import os
from web.app import app

if __name__ == "__main__":
  app.run(debug=True, host='0.0.0.0', use_reloader=True, port=int(os.environ.get('PORT', 5000)))
