import db_manager
import time

db = db_manager.DBManager()
time.sleep(1) # wait for connect
print("Conn is:", db.conn)

res = db.register('testuser_888', '1234', 'testnick', 'test@test.com')
print("Register result:", res)
