var createHTTP = function() {
    var http = null;
    if(window.XMLHttpRequest) {         
        try {
            http = new XMLHttpRequest();
        } catch(e) {
        }
    } else if(window.ActiveXObject) {
        try {
            http = new ActiveXObject("Msxml2.XMLHTTP");
        } catch(e) {
            try {
                http = new ActiveXObject("Microsoft.XMLHTTP");
            } catch(e) {
            }
        }
    }

    return http;
}

var getHTTPDocument = function(url, resultCallback) {
    var http = createHTTP();
    http.open('GET', url, true);
    http.onreadystatechange = function() {
        if (http.readyState == 4) {
            if (http.responseText)
                resultCallback(http);
        }
    }
    http.send(null);
}

var createDiv = function(className) {
    var elem = document.createElement('div');
    elem.setAttribute('class', className);
    return elem;
}

var createAnchor = function(url) {
    var e = document.createElement('a');
    e.setAttribute('href', url);
    return e;
}

var createImage = function(url, alt) {
    var e = document.createElement('img');
    e.setAttribute('src', url);
    e.setAttribute('alt', alt);
    return e;
}

var createTextDiv = function(className, text) {
    var e = document.createElement('div');
    e.setAttribute('class', className);
    if (typeof text == 'string')
        e.appendChild(document.createTextNode(text));
    else if (text != null)
        e.appendChild(text);
    return e;
}

var createTextSpan = function(className, text) {
    var e = document.createElement('span');
    e.setAttribute('class', className);
    if (typeof text == 'string')
        e.appendChild(document.createTextNode(text));
    else if (text != null)
        e.appendChild(text);
    return e;
}

var getElementByName = function(node, name) {
    if (node.nodeType == Node.ELEMENT_NODE && node.nodeName == name)
        return node;
    for (var i = 0; i < node.childNodes.length; i++) {
        var child = getElementByName(node.childNodes[i], name);
        if (child)
            return child;
    }
    return null;
}

var getElementText = function(node) {
    if (!node)
        return '';
    if (node.nodeType == Node.TEXT_NODE)
        return node.nodeValue;
    var text = '';
    for (var i = 0; i < node.childNodes.length; i++) {
        text += getElementText(node.childNodes[i]);
    }
    return text;
}

var entities = new Object();
entities['&quot;'] = "\"";
entities['&amp;'] = "&";
entities['&apos;'] = "'";
entities['&lt;'] = "<";
entities['&gt;'] = ">";

var interpretEntities = function(text)
{
    for (var key in entities)
        text = text.replace(new RegExp(key, 'g'), entities[key]);
    return text;
}

var stripTags = function(text)
{
    return text.replace(/<[^>]*>/g, '');
}

var GalleryItem = function(name, url, image) {
    this.name = name;
    this.url = url;
    this.image = image;
}

var Gallery = function(container, maxRows, cols) {
    this.container = container;
    this.maxRows = maxRows;
    this.cols = cols
    this.items = null;
    this.tableElement = null;
    this.random = false;
    this.start = 0;
}

Gallery.prototype.setButtons = function(prev, next) {
    var obj = this;
    this.prevButton = prev;
    this.nextButton = next;
    prev.onclick = function() {obj.prevPage();}
    next.onclick = function() {obj.nextPage();}
}

Gallery.prototype.populate = function() {
    var obj = this;
    getHTTPDocument('gallery-items.txt', function(http) {
        obj.onData(http.responseText);
    });
}

Gallery.prototype.onData = function(data) {
    var items = data.split('\n');
    this.items = new Array();
    while (items.length >= 3) {
        this.items.push(
            new GalleryItem(items.shift(), items.shift(), items.shift()));
    }
    this.maxpage = this.items.length - 1;
    if (this.random) {
        this.items.sort(function() {
            return Math.round(Math.random()) * 2 - 1;
        })
    }
    this.repopulate();
}

Gallery.prototype.repopulate = function() {
    if (this.tableElement) {
        this.container.removeChild(this.tableElement);
        this.tableElement = null;
    }

    var i = this.start;
    var tableElement = document.createElement('table');
    tableElement.setAttribute('class', 'gallery');
    tableBody = document.createElement('tbody');
    tableElement.appendChild(tableBody);
    for (var row = 0; row < this.maxRows; row++) {
        var rowElement = document.createElement('tr');
        for (var col = 0; col < this.cols; col++) {
            var cellElement = document.createElement('td');
            var item = this.items[i];
            if (item) {
                var itemAnchor = createAnchor(item.url);
                itemAnchor.appendChild(
                    createImage(item.image + '?display=thumb', item.name));
                itemAnchor.appendChild(
                    createTextDiv('gallery-label', item.name));
                cellElement.appendChild(itemAnchor);
            }
            rowElement.appendChild(cellElement);
            i += 1;
        }
        tableBody.appendChild(rowElement);
    }
    this.container.appendChild(tableElement);
    this.tableElement = tableElement;
}

Gallery.prototype.prevPage = function() {
    this.start = Math.max(0, this.start - 1);
    this.repopulate();
}

Gallery.prototype.nextPage = function() {
    this.start = Math.max(0, Math.min(this.start + 1, this.maxpage));
    this.repopulate();
}

var Discussion = function(container) {
    this.container = container;
}

Discussion.prototype.populate = function() {
    var obj = this;
    getHTTPDocument('pyglet-users.xml', function(http) {
        obj.onData(http.responseXML);
    });
}

Discussion.prototype.onData = function(doc) {
    feed = doc.documentElement;
    for (var i = 0; i < feed.childNodes.length; i++) {
        var entry = feed.childNodes[i];
        if (entry.nodeType != Node.ELEMENT_NODE || entry.nodeName != 'entry')
            continue;

        var name = getElementText(getElementByName(entry, 'name'));
        var title = getElementText(getElementByName(entry, 'title'));
        var summary = getElementText(getElementByName(entry, 'summary'));
        summary = interpretEntities(stripTags(summary));
        this.addEntry(name, title, summary);
    }
}

Discussion.prototype.addEntry = function(name, title, summary) {
    var entry = createDiv('discussion-entry');
    this.container.appendChild(entry);
    
    titleElement = createTextSpan('discussion-title', title);
    entry.appendChild(titleElement);
    entry.appendChild(document.createTextNode(summary));
    nameElement = createTextSpan('discussion-attribution', 'Posted by ' + name);
    entry.appendChild(nameElement);
}
