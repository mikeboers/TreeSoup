# encoding: utf8


try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
    
import copy


def _indent_etree(elem, indent='\t', level=0):
    """Indent the nodes of an ElementTree in place."""
    i = '\n' + level * indent
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + indent
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent_etree(elem, indent, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class XML(object):
    
    # To catch infinite loops.
    _element = None
    _etree_attrs = frozenset('''
        get
        tag
        attrib
        keys
        items
    '''.strip().split())
    
    _base_child_class = None
    _attr_child_classes = {}
    
    def _auto_child_class(self, name=None):
        return self.__class__._attr_child_classes.get(name) or self._base_child_class or self.__class__
    
    @classmethod
    def register_attr_class(cls, name):
        def _decorator(fn):
            if '_attr_child_classes' not in cls.__dict__:
                cls._attr_child_classes = {}
            cls._attr_child_classes[name] = fn
            return fn
        return _decorator
    
    def __init__(self, input):
        if isinstance(input, basestring):
            input = etree.XML(input.encode('utf8'))
        self._element = input
    
    
    # We want the text and tail to always be unicode, but ElementTree will
    # only return unicode for these properties if there are non-ascii
    # characters within them. We will force them to unicode.
    
    def _unicode_or_none(name):
        '''Build a property for unicode coercion, but leave None alone.'''
        @property
        def _prop(self):
            x = getattr(self._element, name)
            return unicode(x) if not isinstance(x, unicode) else x
        return _prop
    
    text = _unicode_or_none('text')
    tail = _unicode_or_none('tail')
    
    del _unicode_or_none
    
    @property
    def content(self):
        """The XML source of all the contents of this tag."""
        return self.text + ''.join(str(x) for x in self) + self.tail

    def __getitem__(self, name):
        if isinstance(name, int):
            return self._auto_child_class()(self._element[name])
        return self._element.attrib[name]

    def __getattr__(self, name):
        if name in self._etree_attrs:
            return getattr(self._element, name)
        res = self._element.find('.//' + name)
        return self._auto_child_class(name)(res) if res is not None else None

    def __call__(self, pattern):
        return [self._auto_child_class()(x) for x in self._element.findall('.//' + pattern)]


    def find(self, pattern):
        return self._auto_child_class()(self._element.find(pattern))

    def findall(self, pattern):
        return [self._auto_child_class()(x) for x in self._element.findall(pattern)]

    def to_string(self, pretty=False):
        el = self._element
        if pretty:
            el = copy.deepcopy(el)
            _indent_etree(el)
        return etree.tostring(el)
    
    def __str__(self):
        return self.to_string(True)
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, str(self))
      
    def __reduce__(self):
        # It may not be completely nessesary to do this, but for some reason
        # I feel safer in doing so.
        return self.__class__, (str(self), )
          

def parse(input, class_=XML):
    return class_(input)


if __name__ == '__main__':
    
    import datetime
    import cPickle as pickle
    
    class PhotoXML(XML): pass
    
    @PhotoXML.register_attr_class('dates')
    class PhotoDatesXML(XML):
        
        @property
        def posted(self):
            return datetime.datetime.utcfromtimestamp(int(self['posted']))
            
        @property
        def lastupdate(self):
            return datetime.datetime.utcfromtimestamp(int(self['lastupdate']))
        
        @property
        def taken(self):
            return datetime.datetime.strptime(self['taken'], '%Y-%m-%d %H:%M:%S')
    
    xml = PhotoXML('''<rsp stat="ok"><photo id="4368732797" secret="6279410d6d" server="4032" farm="5" dateuploaded="1266592022" isfavorite="0" license="4" rotation="0" originalsecret="9ee3a31f15" originalformat="jpg" views="1110" media="photo"><owner nsid="12187063@N02" username="*~Dawn~*" realname="" location="Saratoga, California, USA"/><title>I've Been Tagged.</title><visibility ispublic="1" isfriend="0" isfamily="0"/><dates posted="1266592022" taken="2010-02-18 16:56:06" takengranularity="0" lastupdate="1279296487"/><editability cancomment="0" canaddmeta="0"/><usage candownload="1" canblog="0" canprint="0" canshare="0"/><comments>110</comments><notes><note id="72157623342229665" author="7323454@N08" authorname="*~ peedge ~*" x="275" y="173" w="50" h="50">This looks so unreal .. Like liquid metal kinda effect</note><note id="72157623476287744" author="21923086@N05" authorname="Stephen Oachs" x="232" y="134" w="50" h="50">Hot tom boy ;)</note></notes><tags><tag id="12166715-4368732797-411" author="12187063@N02" raw="self portrait" machine_tag="0">selfportrait</tag><tag id="12166715-4368732797-1127671" author="12187063@N02" raw="horse's eye" machine_tag="0">horseseye</tag><tag id="12166715-4368732797-1518294" author="12187063@N02" raw="I DARE YOU" machine_tag="0">idareyou</tag><tag id="12166715-4368732797-52406650" author="12187063@N02" raw="TO DO THIS TOO" machine_tag="0">todothistoo</tag><tag id="12166715-4368732797-8524" author="8943680@N04" raw="Whiskey" machine_tag="0">whiskey</tag><tag id="12166715-4368732797-7062" author="8943680@N04" raw="Bat" machine_tag="0">bat</tag></tags><urls><url type="photopage">http://www.flickr.com/photos/naturesdawn/4368732797/</url></urls></photo></rsp>''')    
    print repr(xml.dates), xml.dates.posted, xml.dates.taken, xml.dates.lastupdate

    
    xml = parse(u'<title>¡™£</title>')
    print repr(xml.text), xml.text
    print repr(xml.tag), xml.tag
    
