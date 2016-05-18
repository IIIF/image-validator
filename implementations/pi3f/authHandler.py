
from bottle import request, response, abort, redirect
from bottle import auth_basic, parse_auth

import json
import urllib, urllib2

class AuthHandler(object):

    def __init__(self, application):
        self.application = application
        self.config = application.config

    def check_auth(self):
        cf = self.config
        if cf.DEGRADE_IMAGES or cf.AUTH_TYPE:
            hasCookie = request.get_cookie(cf.COOKIE_NAME, secret=cf.COOKIE_SECRET)   
            authToken = request.headers.get('Authorization', '')
            hasToken = self.check_token(authToken)
            return hasCookie or hasToken        
        else:
            return True

    def check_token(self, token):
        if not token.startswith("Bearer "):
            return False
        tok = token[7:]
        # FIXME Implement tokens!
        return True

    def noaccess(self):
        cf = self.config
        noacc = {"@context": "http://iiif.io/api/image/2/context.json", "@id": cf.BASEPREF+"no-access", "protocol": "http://iiif.io/api/image", "height": 1, "width": 1, "service": {"@context": "http://iiif.io/api/auth/1/context.json", "@id": cf.BASEPREF+"login", "profile":"iiif:auth-service"}}
        response['Access-Control-Allow-Origin'] = '*'
        return self.application.send(json.dumps(noacc), ct="application/json")

    def get_iiif_token(self):
        # This is the next step -- client requests a token to send to info.json
        # We're going to just copy it from our cookie.
        # postMessage request to get the token to send to info.json in Auth'z header
        cf = self.config
        callback = request.query.get('browser', '')
        authcode = request.query.get('code', '')
        account = ''
        try:
            account = request.get_cookie(cf.COOKIE_NAME_ACCOUNT, secret=cf.COOKIE_SECRET)
            response.delete_cookie(cf.COOKIE_NAME_ACCOUNT)
        except:
            pass
        if not account:
            data = {"error":"missingCredentials","description": "No login details received"}
        else:
            data = {"accessToken":account, "tokenType": "Bearer", "expiresIn": 3600}
            # Set the cookie for the image content
            response.set_cookie(cf.COOKIE_NAME, account, secret=cf.COOKIE_SECRET)
        dataStr = json.dumps(data)

        if callback:
            html = """<html><body><script>
window.opener.postMessage({0}, '*');    
window.close();
</script></body></html>""".format(dataStr)
            return self.application.send(html, ct="text/html")
        else:
            return self.application.send(dataStr, ct="application/json")

    def logout(self):
        cf = self.config
        response.delete_cookie(cf.COOKIE_NAME_ACCOUNT)
        response.delete_cookie(cf.COOKIE_NAME)
        response['Access-Control-Allow-Origin'] = '*'
        return self.application.send("<html><script>window.close();</script></html>", status=401, ct="text/html");

    def get_client_code(self):
        cf = self.config
        if not cf.CLIENT_SECRETS:
            abort(404)

        bod = request.body.read()
        js = json.loads(bod)
        name = js['clientId']
        secret = js['clientSecret']
        if cf.CLIENT_SECRETS.get(name, '') == secret:
            data = {'authorizationCode' : code}
        else:
            data = {'error': 'invalidClientSecret'}
        dataStr = json.dumps(dataStr)            
        return self.application.send(dataStr, ct="application/json")    

class NullAuthHandler(AuthHandler):

    def check_auth(self):
        return True

class BasicAuthHandler(AuthHandler):
    def check_basic_auth(user, password):
        # Re-implement me to do actual user/password checking
        return user == password

    @auth_basic(check_basic_auth)
    def login(self):
        cf = self.config
        auth = request.headers.get('Authorization')
        email,p = parse_auth(auth)      
        response.set_cookie(cf.COOKIE_NAME_ACCOUNT, email, secret=cf.COOKIE_SECRET)
        return self.application.send("<html><script>window.close();</script></html>", ct="text/html");

class OAuthHandler(AuthHandler):

    def _get_token(self):
        # Google OAuth2 helpers
        cf = self.config
        params = {
            'code': request.query.get('code'),
            'client_id': cf.GOOGLE_API_CLIENT_ID,
            'client_secret': cf.GOOGLE_API_CLIENT_SECRET,
            'redirect_uri': cf.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        payload = urllib.urlencode(params)
        url = cf.GOOGLE_OAUTH2_URL + 'token'
        req = urllib2.Request(url, payload) 
        return json.loads(urllib2.urlopen(req).read())

    def _get_data(self, response):
        params = {
            'access_token': response['access_token'],
        }
        payload = urllib.urlencode(params)
        url = self.config.GOOGLE_API_URL + 'userinfo?' + payload
        req = urllib2.Request(url)  # must be GET
        return json.loads(urllib2.urlopen(req).read())

    def login(self):
        # OAuth starts here. This will redirect User to Google
        cf = self.config
        params = {
            'response_type': 'code',
            'client_id': cf.GOOGLE_API_CLIENT_ID,
            'redirect_uri': cf.GOOGLE_REDIRECT_URI,
            'scope': cf.GOOGLE_API_SCOPE,
            'state': request.query.get('next'),
        }
        url = cf.GOOGLE_OAUTH2_URL + 'auth?' + urllib.urlencode(params)
        response['Access-Control-Allow-Origin'] = '*'
        redirect(url)

    def home(self):
        # OAuth ends up back here from Google. This sets a cookie and closes window
        # to trigger next step
        cf = self.config
        resp = self._get_token()
        data = self._get_data(resp)

        first = data.get('given_name', '')
        last = data.get('family_name', '')
        email = data.get('email', '')
        name = data.get('name', '')
        pic = data.get('picture', '')
        response.set_cookie(cf.COOKIE_NAME_ACCOUNT, email, secret=cf.COOKIE_SECRET)
        return self.application.send("<html><script>window.close();</script></html>", ct="text/html");

