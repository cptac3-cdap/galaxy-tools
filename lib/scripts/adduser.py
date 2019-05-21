import sys
sys.path.append('scripts')                                                                                 
sys.path.append('lib')                                                                                 
from db_shell import *
from galaxy.web.security import get_random_bytes

user = sa_session.query( User ).enable_eagerloads( False ).filter_by( email=sys.argv[1] ).first()
if not user:
    u = User(email=sys.argv[1])
    u.set_password_cleartext(sys.argv[2])
    u.username = sys.argv[1].split('@')[0]
    sa_session.add(u)
    sa_session.flush()
    apikey = APIKeys()
    apikey.user_id = u.id
    if len(sys.argv) >= 4:
        apikey.key = sys.argv[3]
    else:
        apikey.key = get_random_bytes(16)
    sa_session.add(apikey)
    sa_session.flush()
    role = Role( name=u.email, description='Private Role for ' + u.email, type=Role.types.PRIVATE )
    sa_session.add( role )
    sa_session.flush()
    assoc = UserRoleAssociation( u, role )
    sa_session.add( assoc )
    sa_session.flush()
else:
    print >>sys.stderr, "Email address %s already in use"%(sys.argv[1],)    

