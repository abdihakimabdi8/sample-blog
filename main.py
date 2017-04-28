import os
import webapp2
import jinja2
import cgi
import re
from google.appengine.ext import db
template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)
def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class Handler(webapp2.RequestHandler):
    def render_str(template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
class MainPage(Handler):
  def get(self):
      t = jinja_env.get_template("user-signup.html")
      content = t.render(error=self.request.get("error"))
      self.response.write (content)
class UserVerify(Handler):
    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        confirm_password = self.request.get("confirm")
        email =self.request.get("email")
        have_error = False
        params = dict(username = username,
                      email = email)
        if not valid_username(username):
            params['error_username'] = " Please provide valid username"
            have_error = True

        if not valid_password(password):
            params['error_password'] = " Please provide valid password"
            have_error = True

        if (confirm_password == password)==False:
            params['error_verify'] = "Password Verification failed"
            have_error = True
        if not valid_email(email):
            params['error_verify'] = " Please provide valid E-mail"
            have_error = True
        if have_error:
            self.render('user-signup.html', **params)
        else:


            self.redirect('/blog?username=' + username)
class Post(db.Model):
    title = db.StringProperty(required = True)
    body = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    def render(self):
        self.body = self.body.replace('\n', '<br>')
        return render_str("post.html", p = self)

class HomePage(Handler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM Post  order by created desc LIMIT 5")
        t = jinja_env.get_template("front.html")
        content = t.render(posts = posts)
        self.response.write(content)

class PostHandler(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        t = jinja_env.get_template("permalink.html")
        content = t.render(post = post)
        self.response.write(content)
class NewPost(Handler):
    def get(self):

        t = jinja_env.get_template("newpost.html")
        content = t.render(post = self)
        self.response.write(content)
    def post(self):
        title = self.request.get("title")
        body = self.request.get("body")
        if title and body:
            post = Post(parent=blog_key(), title=title, body=body)
            post.put()
            self.redirect('/blog/%s' % str(post.key().id()))
        else:
            error = "subject and content, please!"
            t = jinja_env.get_template("newpost.html")
            content = t.render(title=title, body=body, error = error)
            self.response.write(content)


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/userverify', UserVerify),
    ('/blog/?', HomePage),
    ('/blog/([0-9]+)', PostHandler),
    ('/blog/newpost', NewPost),

], debug=True)
