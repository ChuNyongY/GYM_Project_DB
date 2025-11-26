import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='cny990803',
    database='gym_management',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()

print("\n=== 회원 데이터 확인 ===")
cursor.execute('SELECT member_id, member_rank, name, locker_type, uniform_type, checkin_time, checkout_time FROM members ORDER BY member_id')
members = cursor.fetchall()

for row in members:
    print(f"ID: {row['member_id']}, Rank: {row['member_rank']}, Name: {row['name']}, Locker: {row['locker_type']}, Uniform: {row['uniform_type']}, CheckIn: {row['checkin_time']}, CheckOut: {row['checkout_time']}")

conn.close()
