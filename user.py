import uuid
# User class
class User():
    def __init__(self, full_name, username, password, role, id="", verified=False):
        # Main initialiser
        self.full_name = full_name
        self.username = username
        self.password = password
        self.role = role
        self.id = uuid.uuid4().hex if not id else id
        self.verified = verified
    
    @classmethod
    def make_from_dict(cls, d):
        # Initialise User object from a dictionary
        return cls(d['full_name'], d['username'], d['password'], d['role'], d['id'], d['verified'])

    def dict(self):
        # Return dictionary representation of the object
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "verified": self.verified
        }
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

# Anonymous user class
class Anonymous():

    @property
    def is_authenticated(self):
        return False

    @property
    def is_active(self):
        return False

    @property
    def is_anonymous(self):
        return True

    def get_id(self):
        return None