# 포함관계(in , not in)
# if role == 'admin' or role =='manager' or role == 'staff'

#alloewed_roles = ['admin' ,'manager' , 'staff']

role = 'admin'
if role in ['admin', 'manager', 'staff']:
    print('접근 허용')
else:
    print('접근 불가')   
    
