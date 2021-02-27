from app import db, Users

db.create_all()

new_user = Users(username="admin", password="9f3adc4ea3dfdb7f9f42fc4968388304ac8e0b68afa0351e6ab734837f37ebae", mod_=1, admin_=1)
db.session.add(new_user)  # adds content to database
db.session.commit()

new_user = Users(username="user", password="d7dbb0f0e3699dcefcce15473f1c2a45c450ab1bb21c937ac3fb1f8d441a1686")
db.session.add(new_user)  # adds content to database
db.session.commit()