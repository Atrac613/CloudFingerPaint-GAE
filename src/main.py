import os
import hashlib
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images
from django.utils import simplejson 

class CloudFingerPaint(db.Model):
    image = db.BlobProperty()
    queue_flag = db.BooleanProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now_add=True)

class HomePage(webapp.RequestHandler):
    def get(self):

        template_values = {
        }
          
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))

class APITestPage(webapp.RequestHandler):
    def get(self):

        template_values = {
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/api_test.html')
        self.response.out.write(template.render(path, template_values))

class UploadAPI(webapp.RequestHandler):
    def post(self):
        
        data = {}
        image = self.request.get('image')
        if image is not None:
            cloud_finger_paint = CloudFingerPaint()
            cloud_finger_paint.image = db.Blob(image)
            cloud_finger_paint.queue_flag = True
            cloud_finger_paint.put()
            
            data = {'status': True}
        else:
            data = {'status': False}
            
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)

class GetQueueListAPI(webapp.RequestHandler):
    def get(self):

        cloud_finger_paint_query = CloudFingerPaint.all()
        cloud_finger_paint_query.filter('queue_flag =', True)
        queue_list = cloud_finger_paint_query.fetch(10)
        
        data = []
        
        for queue in queue_list:
            if hashlib.sha1(queue.image).hexdigest() != '5d3ab391d2559dfa5edd8bdd65c0b1f56ee27f62':
                data.append({'id': queue.key().id(), 'image_url': 'http://cloud-finger-paint.appspot.com/api/get_image?id=%s' % queue.key().id()})
        
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)

class GetImageAPI(webapp.RequestHandler):
    def get(self):
      
        image_id = self.request.get('id')
        if image_id == '':
            return self.error(404)
        
        cloud_finger_paint = CloudFingerPaint.get_by_id(int(image_id))
        
        if cloud_finger_paint is None:
            return self.error(404)
        
        logging.info('sha1: %s' % hashlib.sha1(cloud_finger_paint.image).hexdigest())
        if hashlib.sha1(cloud_finger_paint.image).hexdigest() == '5d3ab391d2559dfa5edd8bdd65c0b1f56ee27f62':
            return self.error(404)
          
        img = images.Image(cloud_finger_paint.image)
        img.resize(height=400)
        img.im_feeling_lucky()
        thumbnail = img.execute_transforms(output_encoding=images.PNG)
        
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(thumbnail)
        
        return
  
class UpdateQueueFlagAPI(webapp.RequestHandler):
    def get(self):

        image_id = self.request.get('id')
        if image_id == '':
            return self.error(404)
        
        flag = self.request.get('flag')
        
        cloud_finger_paint = CloudFingerPaint.get_by_id(int(image_id))
        
        if cloud_finger_paint is None or flag is None:
            data = {'status': False}
        else:
            if flag == 'True':
                cloud_finger_paint.queue_flag = True
            else:
                cloud_finger_paint.queue_flag = False
                
            cloud_finger_paint.put()
        
            data = {'status': True}
            
        json = simplejson.dumps(data, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)

application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/api_test', APITestPage),
                                      ('/api/upload', UploadAPI),
                                      ('/api/get_queue_list', GetQueueListAPI),
                                      ('/api/get_image', GetImageAPI),
                                      ('/api/update_queue_flag', UpdateQueueFlagAPI)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()