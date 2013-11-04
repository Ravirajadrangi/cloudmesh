from ConfigParser import SafeConfigParser
from cloudmesh.config.cm_config import cm_config, cm_config_server
from cloudmesh.util.keys import get_fingerprint
from cloudmesh.provisioner.provisioner import *
from cloudmesh.user.cm_user import cm_user
from cloudmesh.user.cm_userLDAP import cm_userLDAP, get_ldap_user_from_yaml
from cloudmesh.user.roles import Roles
from cloudmesh.util.util import banner, cond_decorator, path_expand
from datetime import datetime
from flask import Flask, current_app, request, session, Flask, render_template, \
    flash, send_from_directory, redirect, g
from flask.ext.login import LoginManager, login_user, logout_user, \
    login_required, current_user, UserMixin, login_required
from flask.ext.principal import Principal, Identity, AnonymousIdentity, \
    identity_changed, Permission, identity_loaded, RoleNeed, UserNeed
from flask.ext.wtf import Form, TextField, PasswordField, Required, Email
from flask.ext.principal import Permission, RoleNeed

from flask.ext.rstpages import RSTPages
from pprint import pprint
import cloudmesh
import os
import pkg_resources
import requests
import sys
import sys
import time
import traceback
import types
import webbrowser



admin_permission = Permission(RoleNeed('admin'))


# from flask.ext.autoindex import AutoIndex

sys.path.insert(0, '.')
sys.path.insert(0, '..')


# ============================================================
# DYNAMIC MODULE MANAGEMENT
# ============================================================

all_modules = ['menu',
               'pbs',
               'launch',
               'nose',
               'inventory',
               'provisioner',
               'keys',
               'profile',
               'git',
               'cloud',
               #'workflow',
               'mesh',
               'mesh_hpc',
               'users',
               'status',
               # 'register',
               'metric'
                ]

s_config = cm_config_server()


with_browser = s_config.get("cloudmesh.server.webui.browser")
browser_page = s_config.get("cloudmesh.server.webui.page")
host = s_config.get("cloudmesh.server.webui.host")
port = s_config.get("cloudmesh.server.webui.port")

# load home page if no page specified
if browser_page:
    url_link = "http://{0}:{1}/{2}".format(host, port, browser_page)
else:
    url_link = "http://{0}:{1}".format(host, port)

webbrowser.register("safari", None)


# from cloudmesh.util.webutil import setup_imagedraw

with_rack = s_config.get("cloudmesh.server.rack.with_rack")

if with_rack:
    all_modules.append('rack')
else:
    log.info("The Rack diagrams are not enabled")

# exclude_modules = ['flatpages']
exclude_modules = []

modules = [m for m in all_modules if m not in exclude_modules]

for m in modules:
    log.debug("Import module {0}".format(m))
    exec "from modules.{0} import {0}_module".format(m)


# ============================================================
# DYNAMIC MODULE MANAGEMENT
# ============================================================

debug = True

with_cloudmesh = False

# ============================================================
# allowing the yaml file to be written back upon change
# ============================================================

with_write = True

# ============================================================
# setting up reading path for the use of yaml
# ============================================================

default_path = '.futuregrid/cloudmesh.yaml'
home = os.environ['HOME']
filename = "%s/%s" % (home, default_path)

# ============================================================
# global vars
# ============================================================
config = cm_config_server()

SECRET_KEY = config.get('cloudmesh.server.webui.secret')
DEBUG = debug


# ============================================================
# STARTING THE FLASK APP
# ============================================================

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = debug

# Added for loop control; break, continue
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

pages = RSTPages(app)

# dynamic app loading from defined modules
# app.register_blueprint(keys_module, url_prefix='',)

for m in modules:
    log.debug("Loading module {0}".format(m))
    exec "app.register_blueprint({0}_module, url_prefix='',)".format(m)

principals = Principal(app)
login_manager = LoginManager(app)

admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))
rain_permission = Permission(RoleNeed('rain'))

app.secret_key = SECRET_KEY

# Production logging... send errors via email.
# TODO: Make this configurable.
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('localhost',
                               'cloudmesh-server@cloudmesh.futuregrid.org',
                               ['cm-errors'],
                               'CloudMesh Server Error')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))

# @app.context_processor
# def inject_pages():
#    return dict(pages=pages)
# app.register_blueprint(menu_module, url_prefix='', )
# if debug:
#    AutoIndex(app, browse_root=os.path.curdir)

# ============================================================
# VERSION
# ============================================================

version = pkg_resources.get_distribution("cloudmesh").version

@app.context_processor
def inject_version():
    return dict(version=version)


# ============================================================
# ROUTE: /test
# ============================================================

#

'''
@app.route('/test')
@login_required
def restricted_index():
    return render_template('index.html')
'''

@app.route('/rain')
@login_required
@rain_permission.require(http_exception=403)
def rain_index():
    return render_template('sample/rain.html')


@app.route('/admin')
@login_required
@admin_permission.require(http_exception=403)
def admin_index():
    return render_template('admin/admin.html')


# ============================================================
# ROUTE: erros
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    error = 'This page does not exist {0}'.format(404)
    return render_template('error.html',
                           error=error,
                           type="Page not found",
                           msg="")

@app.errorhandler(403)
def page_not_found(error):
    error = 'Access denied {0}'.format(403)
    return render_template('error.html',
                           error=error,
                           type="Authorization Denied",
                           msg="You are not authorized to access this page.\n"
                               "This may happen if you have not logged in or \n"
                               "If you are not allowed to access this page\n"
                               "as you are not member of the proper role."
                           )
@app.errorhandler(401)
def page_not_found(error):
    error = 'Access denied {0}'.format(401)
    return render_template('error.html',
                           error=error,
                           type="Authentication Denied",
                           msg="You need to login first")




# ============================================================
# ROUTE: /
# ============================================================


@app.route('/')
def index():
    return render_template('index.html')


# ============================================================
# FILTER: timesince
# ============================================================

@app.template_filter()
def timesince(dt, format="float", default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """
    if dt == "None" or dt == "" or dt == None or dt == "completed":
        return "completed"

    # now = datetime.utcnow()
    now = datetime.now()
    if format == 'float':
        diff = now - datetime.fromtimestamp(float(dt))
    else:
        diff = now - dt

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:

        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default

# ============================================================
# FILTER: get_tuple element from string
# ============================================================

@app.template_filter()
def get_tuple_element_from_string(obj, i):
    l = obj[1:-1].split(", ")
    return l[i][1:-1]

# ============================================================
# FILTER: is list
# ============================================================

@app.template_filter()
def is_list(obj):
    return isinstance(obj, types.ListType)

# ============================================================
# FILTER: only numbers
# ============================================================

@app.template_filter()
def only_numbers(str):
    return ''.join(c for c in str if c.isdigit())

# ============================================================
# FILTER: simple_data, cuts of microseconds
# ============================================================

@app.template_filter()
def simple_date(d):
    return str(d).rpartition(':')[0]


# ============================================================
# FILTER: simple_data, cuts of microseconds
# ============================================================

@app.template_filter()
def filter_fingerprint(key):
    return str(get_fingerprint(key))

# ============================================================
# FILTER: state color
# ============================================================

@app.template_filter()
def state_color(state):
    s = state.lower()
    if s == "active":
        color = "#336600"
    else:
        color = "#FFCC99"
    return color

# ============================================================
# FILTER: state style
# ============================================================

@app.template_filter()
def state_style(state):
    color = state_color(state)
    return 'style="background:{0}; font:bold"'.format(color)


# ============================================================
# FILTER: check if roles are allowed
# ============================================================
@app.template_filter()
def role_allowed(user_roles, allowed_roles):
    if 'all' in allowed_roles:
        return True
    for role in user_roles:
        if role in allowed_roles:
            return True
    return False

# ============================================================
# ROUTE: PAGES
# ============================================================


# @app.route('/<path:path>/')
# def page(path):
#    page = pages.get_or_403(path)
#    return render_template('page.html', page=page)


@app.route('/<path:path>/')
def page(path):
    page = pages.get(path)
    return render_template('page.html', page=page)




# ============================================================
#  PRINCIPAL LOGIN
# ============================================================

# if cloudmesh.with_login:
#    idp = cm_userLDAP ()
#    idp.connect("fg-ldap", "ldap")


@app.before_request
def before_request():
    g.user = current_user

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):

    if 'user_id' in session:
        current_user = load_user(session['user_id'])
        # Set the identity user object
        identity.user = current_user

        # Add the UserNeed to the identity
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # Assuming the User model has a list of roles, update the
        # identity with the roles that the user provides
        if hasattr(current_user, 'roles'):
            for role in current_user.roles:
                identity.provides.add(RoleNeed(role))

    """
    identity.provides.add(RoleNeed("rain"))
    """

@login_manager.user_loader
def load_user(id):
    try:
        # load from yaml the roles and check them
        role_server = Roles()
        roles = role_server.get(id)
        return User(id, id, roles)
    except:
        # TODO: this could bea bug
        return None

class User(UserMixin):

    def __init__(self, name, id, roles=['user'], active=True):
        self.name = name
        self.id = id
        self.active = active
        self.roles = roles
        self._cm_info = None

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def is_authenticated(self):
        return True

    def cm_info(self):
        if self._cm_info is None:
            cmu = cm_user()
            self._cm_info = cmu.info(self.id)
            cmu.init_defaults(self.id)
        return self._cm_info

    def cm_profile(self):
        return self.cm_info()['profile']

    def cm_clouds(self):
        return self.cm_info()['clouds']

class LoginForm(Form):

    username = TextField()
    password = PasswordField()

    def validate_on_submit(self):
        return True



@app.route('/login', methods=['GET', 'POST'])
def login():

    error = None
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():

        form.error = None
        try:
            # idp = cm_userLDAP ()
            # idp.connect("fg-ldap", "ldap")
            # user = idp.find_one({'cm_user_id': form.username.data})
            # print "MONGO USER"

            # banner("LDAPUSER")
            # pprint (user)


            banner("CM_USER")
            user_obj = cm_user()
            user = user_obj.info(form.username.data)


        except Exception, e:
            print traceback.format_exc()
            error = "LDAP server not reachable"
            error += str(e)
            return render_template('error.html',
                           form=form,
                           type="Can not reach LDAP",
                           msg="")



        if user is None:
            form.error = 'Login Invalid'
        elif user['cm_user_id'] != form.username.data:
            form.error = 'Login Invalid'
        elif user_obj.authenticate(form.username.data, form.password.data):
            print "LOGIN USER"
            g.user = load_user(form.username.data)

            ret = login_user(g.user)

            identity_changed.send(current_app._get_current_object(),
                                      identity=Identity(g.user.id))

            return redirect(request.args.get('next') or '/')
        else:
            form.error = 'Login Invalid'

    return render_template('user/login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    # Remove the user information from the session
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(request.args.get('next') or '/')



if with_browser:
    log.debug("Web page update {0}".format(browser_page))

    webbrowser.register("safari", None)
    webbrowser.open(url_link, 2, autoraise=True)



if __name__ == "__main__":
    # setup_imagedraw()
    # setup_plugins()
    # setup_noderenderers()
    web_host = config.get('cloudmesh.server.webui.host')
    web_port = config.get('cloudmesh.server.webui.port')
    app.run(host=web_host, port=web_port)

    #
    # for debugging
    #

    """
    # SHOULD BE IN A THERAD
    
    with_browser = s_config.get("cloudmesh.server.webui.browser")
    browser_page = s_config.get("cloudmesh.server.webui.page")
    host = s_config.get("cloudmesh.server.webui.host")
    port = s_config.get("cloudmesh.server.webui.port")
    url_link = "http://{0}:{1}/{2}".format(host, port, browser_page)

    webbrowser.register("safari", None)
    webbrowser.open(url_link, 2, autorise=True)
    if with_browser:
        log.debug("Web page update {0}".format(browser_page))

        not_found = True
        counter = 0
        while not_found and  (counter < 10):
            checkpage = None
            try:
                log.debug("Check if server is ready")
                checkpage = requests.get(url_link)
                not_found = False
            except Exception, e:
                print e
                print "B PAGE NOT YET READY"
                time.sleep(1)
            counter = counter + 1
    """
