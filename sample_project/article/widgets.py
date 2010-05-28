from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

class FilePickerForm(forms.Textarea):
    def render(self, name, value, attrs=None):
        rendered = super(FilePickerForm, self).render(name, value, attrs)
        url = reverse("file-list-article-image");
        return rendered + mark_safe(u'''<script type="text/javascript">
            $(document).ready(function() {
                var overlay = $('<div>').addClass('file-picker-overlay').overlay({
                    effect: 'apple',
                    speed: 'fast',
                    onLoad: function() {
                        this.getOverlay().data('filePicker').load();
                    }
                }).filePicker({
                    url: '%s',
                    onImageClick: function(e, insert) {
                        insertAtCaret('id_%s', insert);
                    }
                }).appendTo($('body'));
                var anchor = $('<a>').text('Add Image').attr({
                    'id': 'file-picker',
                    'name': 'file-picker',
                    'href': '#'
                }).click(function(e) {
                    e.preventDefault();
                    $(overlay).data('overlay').load();
                }).prependTo('.form-row.body');
            });
            </script>''' % (url, name))
