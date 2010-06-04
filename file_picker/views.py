import os
import tempfile

from django.utils import simplejson as json
from django.http import HttpResponse, HttpResponseServerError
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import UploadedFile
from django.views.decorators.csrf import csrf_exempt

from file_picker.forms import QueryForm, model_to_AjaxItemForm


class FilePickerBase(object):
    model = None
    form = None
    page_size = 4

    def __init__(self, model):
        self.model = model
        self.form = model_to_AjaxItemForm(self.model)

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urlpatterns = patterns('',
            url(r'^$', self.setup, name='file-picker-%s-%s-init' %
                (self.model._meta.app_label, self.model._meta.module_name)
            ),
            url(r'^files/$', self.list, name='file-picker-%s-%s-list' %
                (self.model._meta.app_label, self.model._meta.module_name)
            ),
            url(r'^upload/file/$', self.upload_file, 
                name='file-picker-%s-%s-upload' % 
                (self.model._meta.app_label, self.model._meta.module_name)
            ),
        )
        return urlpatterns
    urls = property(get_urls)
    
    def setup(self, request):
        data = {}
        urls = {
            'browse': {'files': reverse('file-picker-%s-%s-list' %
                (self.model._meta.app_label, self.model._meta.module_name)
            )},
            'upload': {'file': reverse('file-picker-%s-%s-upload' %
                (self.model._meta.app_label, self.model._meta.module_name)), 
                'form': '' },
        }
        data['urls'] = urls
        return HttpResponse(json.dumps(data), mimetype='application/json')
    
    def append(self, obj):
        return {'name': unicode(obj), 'url': obj.file.url}

    def get_queryset(self,search):
        return self.model.objects.all()

    @csrf_exempt
    def upload_file(self, request):
        if request.GET and 'name' in request.GET:
            name, ext = os.path.splitext(request.GET['name'])
            fn = tempfile.NamedTemporaryFile(prefix=name, suffix=ext, delete=False)
            fn.write(request.raw_post_data)
            fn.close()
            return HttpResponse(fn.name, mimetype='application/json')
        else: 
            if request.POST:
                form = self.form(request.POST)
                if form.is_valid():
                    obj = form.save()
                    data = self.append(obj)
                    return HttpResponse(
                        json.dumps(data), mimetype='application/json'
                    )
            else:
                form = self.form()
            form_str = form.as_table()
            data = { 'form': form_str }
            return HttpResponse(json.dumps(data), mimetype='application/json') 

    def list(self, request):
        form = QueryForm(request.GET)
        if not form.is_valid():
            return HttpResponseServerError()
        page = form.cleaned_data['page']
        result = []
        qs = self.get_queryset(form.cleaned_data['search'])
        pages = Paginator(qs, self.page_size)
        try:
            page_obj = pages.page(page)
        except EmptyPage:
            return HttpResponseServerError()
        for obj in page_obj.object_list:
            result.append(self.append(obj))
        data = {
            'page': page,
            'pages': pages.page_range,
            'search': form.cleaned_data['search'],
            'result': result,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
        return HttpResponse(json.dumps(data), mimetype='application/json')

