import os
import json
import base64
import traceback
import xml.etree.ElementTree as ET

from tqdm import tqdm

from aardwolf.keyboard import KeyboardLayout, VK_MODIFIERS

"""
This script will fetch all keyboard layouts from https://kbdlayout.info/ and parse the results.
Results will be stored in a JSON format to be consumed by the 'KeyboardLayout' class.
As I do not control the website, I can't guarantee that this script will work in the future.

"""

def full_refresh():
    loc_info = {}
    import re
    import urllib.request, urllib.error, urllib.parse
    
    klids_to_filename = {}
    names_to_filename = {}
    shortnames_to_filename = {}


    dirname = os.path.dirname(__file__)
    layout_dir_path = os.path.join(dirname,'layouts/')
    layout_manager_py_path = os.path.join(dirname,'layoutmanager.py')
    with open(layout_dir_path + '__init__.py' , 'w') as f:
        f.write('')
    


    dlocations = {}
    url = 'https://kbdlayout.info/'
    response = urllib.request.urlopen(url)
    webContent = response.read().decode('UTF-8')
    
    #print(webContent)
    hrefs = re.findall(r'href=[\'"]?([^\'" >]+)', webContent)
    for href in hrefs:
        if href.startswith('/00') is True or href.startswith('/k') is True or href.startswith('/K') is True:
            dlocations[href[1:-1]] = 1

    pbar = tqdm(dlocations)
    i = 0
    for loc in pbar:
        #i += 1
        #if i == 10:
        #    break
        try:
            iurl = url + '/' + loc +'/'
            #print('Fetching url: %s' % kurl)
            response = urllib.request.urlopen(iurl)
            webContent = response.read().decode('UTF-8')
        
            match = re.findall(r'(?<=<th>KLID</th><td>)(.*)(?=</td>|$)', webContent)
            if match != '':
                pbar.set_description('Processing %s' % ','.join(match)[:50].ljust(50))
                loc_info[loc] = match        
            else:
                loc_info[loc] = []

            murl = url + '/' + loc +'/download/cldr'
            response = urllib.request.urlopen(murl)
            webContent = response.read().decode('UTF-8')
            root = ET.fromstring(webContent)
            locale = ''
            names = []
            if 'locale' in root.attrib:
                locale = root.attrib['locale']
            for entry in root:
                if entry.tag == 'names':
                    for name in entry:
                        if name.tag == 'name':
                            if 'value' in name.attrib:
                                names.append(name.attrib['value'])

            kurl = url + '/' + loc +'/download/xml'
            #print('Fetching url: %s' % kurl)
            response = urllib.request.urlopen(kurl)
            webContent = response.read().decode('UTF-8')
            #print('Parsing XML data...')
            layout = kbdlayout_xml_to_kayboardlayout(loc, loc_info[loc], locale, names, webContent)
            fname = 'layout_%s.py' % loc
            layouts_file_path = os.path.join(layout_dir_path,fname)
            
            with open(layouts_file_path, 'w', newline = '') as f:
                layoutdata = 'layoutdata = "%s"\r\n' % base64.b64encode(layout.to_json().encode()).decode()
                f.write(layoutdata)
            

            for klid in loc_info[loc]:
                shortname = klid.split(' ',1)[1][1:-1].replace('-','').lower()
                klids_to_filename[klid] = fname
                shortnames_to_filename[shortname] = fname

            for name in names:
                names_to_filename[name] = fname
            

        except Exception as e:
            print('Error! Parsing failed: %s' % loc)
            traceback.print_exc()
            continue
        
    
    with open(layout_manager_py_path, 'w') as f:
        f.write("""
import json
import base64
import importlib

from aardwolf.keyboard import KeyboardLayout

### Importlib is used here, as there are many keyboard layouts and you probably don't wish to use all of them
### Importing all of them would take a considerable time however, hence dynamic loading

class KeyboardLayoutManager:
    def __init__(self):
        self.klids_to_filename = json.loads(base64.b64decode("%s").decode())
        self.names_to_filename = json.loads(base64.b64decode("%s").decode())
        self.shortnames_to_filename = json.loads(base64.b64decode("%s").decode())
    
    def __layout_loader(self, filename):
        layoutdata = importlib.import_module('aardwolf.keyboard.layouts.%%s' %% filename[:-3])
        return KeyboardLayout.from_layoutdata(layoutdata.layoutdata)


    def get_layout_by_klid(self, klid):
        if klid not in self.klids_to_filename:
            return None
        return self.__layout_loader(self.klids_to_filename[klid])

    def get_layout_by_name(self, name):
        if name not in self.names_to_filename:
            return None
        
        return self.__layout_loader(self.names_to_filename[name]) 
    
    def get_layout_by_shortname(self, name):
        if name not in self.shortnames_to_filename:
            return None
        return self.__layout_loader(self.shortnames_to_filename[name]) 
    
    def get_klids(self):
        for klid in self.klids_to_filename:
            yield klid
    
    def get_names(self):
        for name in self.names_to_filename:
            yield name
    
    def get_shortnames(self):
        for name in self.shortnames_to_filename:
            yield name

if __name__ == '__main__':
    kl = KeyboardLayoutManager()
    kl.get_layout_by_shorname('sq')
""" % (  base64.b64encode(json.dumps(klids_to_filename).encode()).decode(), base64.b64encode(json.dumps(names_to_filename).encode()).decode(), base64.b64encode(json.dumps(shortnames_to_filename).encode()).decode() ))



def kbdlayout_xml_to_kayboardlayout(loc, klids, locale, layout_names, xml_data):
    layout = KeyboardLayout()
    layout.klid = klids
    layout.name = layout_names
    root = ET.fromstring(xml_data)
    #root = tree.getroot()
    #print(root)
    #print(root.tag)
    #print(root.attrib)
    for k in root.attrib:
        if k == 'RightAltIsAltGr':
            layout.RightAltIsAltGr = True if root.attrib[k].lower() == 'true' else False
        elif k == 'ShiftCancelsCapsLock':
            layout.ShiftCancelsCapsLock = True if root.attrib[k].lower() == 'true' else False
        elif k == 'ChangesDirectionality':
            layout.ChangesDirectionality = True if root.attrib[k].lower() == 'true' else False
        else:
            print('Not porcessed attrib key: %s' % k)
            input()
    for child in root:
        for entry in child:
            if entry.tag == 'PK':
                sc = int.from_bytes(bytes.fromhex((entry.attrib['SC'])), byteorder='big', signed = False)
                layout.sc_to_vk[sc] = entry.attrib['VK']
                
                for result in entry:
                    if result.tag == 'Result':
                        extra_with = []
                        if 'With' in result.attrib:
                            extra_with = result.attrib['With'].split(' ')
                        children = list(result.getchildren())
                        for rc in children:
                            if rc.tag == 'DeadKeyTable':
                                process_tag(layout, sc, rc, extra_with)
                        
                        process_tag(layout, sc, result, [])
                        #if 'Text' in result.attrib:
                        #    data = result.attrib['Text']
                        #if 'TextCodepoints' in result.attrib:
                        #    data = result.attrib['TextCodepoints']
                        #
                        #modifiers = 0
                        #if 'With' in result.attrib:
                        #    for wtag in result.attrib['With'].split(' '):
                        #        modifiers |= VK_MODIFIERS[wtag]
                        #
                        #if sc not in layout.sc_to_char:
                        #    layout.sc_to_char[sc] = {}
                        #
                        #if data is not None:
                        #    layout.sc_to_char[sc][modifiers] = data
                        #    layout.char_to_sc[data] = (sc, '')
                        #    if modifiers != 0:
                        #        layout.char_to_sc[data] = (sc, modifiers)
                            
                        
            else:
                print('Unknown tag %s' % entry.tag)
                input()

    return layout

def process_tag(layout, sc, result, extra_with):
    data = None
    if 'Text' in result.attrib:
        data = result.attrib['Text']
    if 'Accent' in result.attrib:
        data = result.attrib['Accent']
    if 'TextCodepoints' in result.attrib:
        data = result.attrib['TextCodepoints']
    
    modifiers = 0
    for wtag in extra_with:
        modifiers |= VK_MODIFIERS[wtag]
    if 'With' in result.attrib:
        for wtag in result.attrib['With'].split(' '):
            modifiers |= VK_MODIFIERS[wtag]
    
    if sc not in layout.sc_to_char:
        layout.sc_to_char[sc] = {}
    
    if data is not None:
        layout.sc_to_char[sc][modifiers] = data
        layout.char_to_sc[data] = (sc, '')
        if modifiers != 0:
            layout.char_to_sc[data] = (sc, modifiers)

if __name__ == '__main__':
    full_refresh()
    #pass