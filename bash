flask db init
flask db migrate -m "Initial migration."
flask db migrate -m "Add SmartBandData model"
flask db upgrade
