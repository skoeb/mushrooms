import dash
import pandas as pd
pd.set_option('chained_assignment', None)

import resources
import functions

server = functions.app.server

if __name__ == '__main__':
    functions.app.run_server(debug=True)