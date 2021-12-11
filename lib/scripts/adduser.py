
import sys, copy
args = copy.copy(sys.argv[1:])
sys.path.append('scripts')
sys.path.append('lib')
sys.argv[1:] = ['galaxy']
from db_shell import *
from galaxy.web.security import get_random_bytes
 
user = sa_session.query( User ).enable_eagerloads( False ).filter_by( email=args[0] ).first()
if not user:
    u = User(email=args[0])
    u.set_password_cleartext(args[1])
    u.username = args[0].split('@')[0]
    sa_session.add(u)
    sa_session.flush()
    apikey = APIKeys()
    apikey.user_id = u.id
    if len(args) >= 3:
        apikey.key = args[2]
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
    print >>sys.stderr, "Email address %s already in use"%(args[0],)    

