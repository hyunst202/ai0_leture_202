class Safeprofile:
    def __init__(self):
        pass
    def get(self,key):
        return True

user_profile = Safeprofile()
if user_profile.get('is_verified'):
    print('성공')
else:
    print('실패')
    
