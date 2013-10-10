import urllib2, urllib, socket, json, cookielib, os, string
from cStringIO import StringIO
import codecs
from optparse import OptionParser


global person_num
global attr_dict
global nameList
nameList = ['schools', 'languages', 'skills', 'previousCompanies']

def commandLineArgs():
    parser = OptionParser()
    parser.add_option( '--config-file', dest = 'config_file',help = 'configuration file in json format')
    parser.add_option('--output-file', dest = 'output_file',help = 'output file stores result in json formate')
    parser.add_option('--temp-dir', dest = 'temp_dir', help = 'temporary dir stores temporary files generated in craweling process')
    (options, args) = parser.parse_args()
    return options
                      
def getElementFromJson(json_obj, path):
    current_obj = json_obj
    result = None
    tmps = path.split('->')
    num = len(tmps)
    
    sec_point = 0
    while sec_point < num:
        section = tmps[sec_point]
        if current_obj.get(section):
            if sec_point == (num -1):
                result = current_obj[section]
            else:
                current_obj = current_obj[section]
            sec_point += 1
        else:
            #print "no content in this section: ", section
            break
    
    return result

def readJsonObjFromFile(file_name, path):
    f = open(file_name, "r")
    s = f.read()
    obj = json.loads(s)
    
    if path is None:
        return obj
    else:
        return getElementFromJson(obj, path)

def getConfig():
    config_file = "conf/config.json"
    output_file = "temp/person_attr.arff"
    temp_dir = "temp"
    
    options = commandLineArgs()
    if options.config_file is not None:
        config_file = str(options.config_file)
    if options.output_file is not None:
        output_file = options.output_file
    if options.temp_dir is not None:
        temp_dir = options.temp_dir
    return config_file, output_file, temp_dir

def init(config_file, temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    for the_file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e
    
    timeout = 30
    socket.setdefaulttimeout(timeout)
    cookie_jar = cookielib.LWPCookieJar()
    cookie = urllib2.HTTPCookieProcessor(cookie_jar)
    proxy_array = readJsonObjFromFile(config_file, "proxy")
    
    if proxy_array is not None:
        num = len(proxy_array)
        if num > 0:
            proxy_conf = {}
            for item in proxy_array:
                proxy_conf[getElementFromJson(item, "protocal")] = getElementFromJson(item,
                        "hostPort")
            proxy = urllib2.ProxyHandler(proxy_conf)
            opener = urllib2.build_opener(proxy, cookie)
        else:
            opener = urllib2.build_opener(cookie)
    else:
        opener = urllib2.build_opener(cookie)

    urllib2.install_opener(opener)
    return opener

def sendRequest(opener, url, param, header, outputfile):
    data_encoded = urllib.urlencode(param)
  
    if header is None:
        if param is None:
            req = urllib2.Request(url)
        else:
            req = urllib2.Request(url, data_encoded)
    else:
        req = urllib2.Request(url, data_encoded, header) 

    response = opener.open(req)
    the_page = response.read()
    if outputfile is not None:
        open(outputfile, "w").write(the_page)
    return the_page

def login(opener, config_file):
    header = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "en-US,en;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "www.linkedin.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36",
        "X-IsAJAXForm": "1",
        "X-Requested-With": "XMLHttpRequest"
    }
    userName = readJsonObjFromFile(config_file, "login->userName")
    password = readJsonObjFromFile(config_file, "login->password")
    url = "https://www.linkedin.com/uas/login-submit"
    login_param = {
            'session_key': userName,
            'session_password': password,
            }
    
    res_content = sendRequest(opener, url, login_param, header, None)
    print res_content
    return

def parseJsonInfo(html_file, line_sign, output_filename):
    for line in html_file.readlines():
        if line_sign in line:
            tmp_str = line.split('<!--')[1]
            tmp_str = tmp_str.split('-->')[0]
            result = tmp_str.decode("utf-8").replace("\\u002d", "-")
            if output_filename is not None:
                file2 = open(output_filename, "w")
                print >> file2, tmp_str 
            return result



def processPerson(opener, person, person_info, temp_dir, output_file):
    person_id = getElementFromJson(person, 'id') 
    str1 = "{\"id\": " + str(person_id) + "}"
    person_obj = json.loads(str1)

    person_obj['firstName'] = getElementFromJson(person, 'firstName') 
    person_obj['lastName'] = getElementFromJson(person, 'lastName') 
    person_obj['location'] = getElementFromJson(person, 'location') 
    

    url = "http://www.linkedin.com/profile/view"
    id_param = {'id': person_id}
    file_name = temp_dir + "/" + str(person_id) + ".html"
    content_str = sendRequest(opener, url, id_param, None, file_name)
    
    person_file = StringIO(content_str)
    if temp_dir is not None:
        file_name = temp_dir + "/" + str(person_id) + "-top_card.json"
    else:
        file_name = None

    top_card = parseJsonInfo(person_file, "top_card-content", file_name)
    if top_card is None:
        return

    tc_obj = json.loads(top_card, 'ISO-8859-1')

    person_attr = {}
    person_obj['headLine'] = getElementFromJson(tc_obj, 'content->BasicInfo->basic_info->memberHeadline')
    person_attr['title'] = person_obj['headLine']

    person_obj['previousCompanies'] = []
    person_attr['previousCompanies'] = []
    pre_positions = getElementFromJson(tc_obj, 'content->TopCard->positionsMpr->topPrevious')
    if pre_positions is not None:
        num =  len(pre_positions)
        person_attr['previousCompanies'] = []
        if num > 0:
            for item in pre_positions:
                person_obj['previousCompanies'].append(item['companyName'])
            person_attr['previousCompanies'] = person_obj['previousCompanies']

    person_obj['educations'] = []

    person_attr['schools'] = []
    person_attr['majors'] = []
    person_attr['degrees'] = []
    
    top_edu = getElementFromJson(tc_obj, 'content->TopCard->educationsMpr->topEducations')
    if top_edu is not None:
        num = len(top_edu)
        
        if num > 0:
            for item in top_edu:
                person_obj['educations'].append({'schoolName': getElementFromJson(item, 'schoolName'), 
                    'major': getElementFromJson(item, 'fieldOfStudy'), 'degree':
                    getElementFromJson(item, 'degree') })
                person_attr['schools'].append(getElementFromJson(item, 'schoolName'))
                person_attr['majors'].append(getElementFromJson(item, 'fieldOfStudy'))
                person_attr['degrees'].append(getElementFromJson(item, 'degree'))

    more_edu = getElementFromJson(tc_obj, 'content->TopCard->educationsMpr->moreEducations')
    if more_edu is not None:
        num = len(more_edu)
        if num > 0:
            for item in top_edu:
                person_obj['educations'].append({'schoolName': getElementFromJson(item, 'schoolName'), 'major': 
                getElementFromJson(item, 'fieldOfStudy'), 'degree': getElementFromJson(item, 'degree') })       
                person_attr['schools'].append(getElementFromJson(item, 'schoolName'))
                person_attr['majors'].append(getElementFromJson(item, 'fieldOfStudy'))
                person_attr['degrees'].append(getElementFromJson(item, 'degree'))

    person_file = StringIO(content_str)
    if temp_dir is not None:
        file_name = temp_dir + "/" + str(person_id) + "-profile.json"
    else:
        file_name = None

    profile = parseJsonInfo(person_file, "profile_v2_background-content", file_name)
    if profile is None:
        return

    profile_obj = json.loads(profile, 'ISO-8859-1')

    person_obj['languages'] = []
    person_attr['languages'] = ['Chinese', 'English']
    langData = getElementFromJson(profile_obj, 'content->Languages->languages->languagesData')
    if langData is not None:
        num = len (langData)
        if num > 0:
            for item in langData:
                person_obj['languages'].append({'lang': getElementFromJson(item, 'lang'), 
                    'level': getElementFromJson(item, 'proficiencyData')})
                person_attr['languages'].append(getElementFromJson(item, 'lang'))

    person_obj['skills'] = []
    skills = getElementFromJson(profile_obj, 'content->Skills->skillsMpr->skills')
    person_attr['skills'] = []
    if skills is not None:
        num = len(skills)
        if num > 0:
            for item in skills:
                person_obj['skills'].append({'skillName': getElementFromJson(item, 'name'), 
                    'endorsementCount': getElementFromJson(item, 'endorsementCount')})
                person_attr['skills'].append(getElementFromJson(item, 'name'))

    pLine = listPersonAttributes(person_attr)
    global person_num
    person_num += 1
    print "No. ", person_num, " : ", pLine, "\n\n"

    output_file.write(pLine)

    person_info.append(person_obj)
    return

def getDegree(degrees):
    degree = None
    for item in degrees:
        if item is None:
            continue
        ditem = string.lower(item)
        if 'bachelor' in ditem:
            ditem = 'bachelor'
        elif 'master' in ditem:
            ditem = 'master'
        elif 'doctor' in ditem:
            ditem = 'doctor'

        if degree == None:
            degree = ditem
        elif degree == 'bachelor' and (ditem == 'master' or ditem == 'doctor'):
            degree = ditem
        elif degree == 'master' and ditem == 'doctor':
            degree = ditem
    return degree

def listPersonAttributes(person_attr):
    
    global nameList
    global attr_dict    

    degree = getDegree(person_attr['degrees'])
    if degree is not None:
        attr_dict['degree'].append(degree)
    else:
        degree = ''
            
    line_str = degree + ','
    
    for featureName in nameList:
        #print person_attr
        feature = person_attr[featureName]
        if feature is not None:
            attr_dict[featureName].extend(feature)
            attr = ';'.join(set(map(lambda x:x.lower(),feature)))
        else:
            attr = ''
        attr = string.replace(attr, ',', ' ')
        line_str += attr + ','
    
    title = person_attr['title']
    if title is not None:
        title = title.split(' at ')[0]
        title = string.replace(title, ',', ' ')
        title = string.lower(title)

        pre_title = ''
        
        if 'senior' in title or 'sr.' in title or 'sr ' in title:
            pre_title = 'senior'
        elif 'assoc.' in title or 'associate' in title:
            pre_title = 'associate principal'
        elif 'principal' in title or 'principle' in title:
            pre_title = 'principal'
        
 
        if 'director' in title or 'vp' in title:
            title = 'director or higher'
        else:
            if 'manager' in title or 'mgr ' in title:
                 title = 'manager'
            elif 'supervisor' in title or 'supv ' in title:
                title = 'supervisor'
            elif 'development' in title:
                title = 'software engineer'
            elif 'engineer' in  title:
                if 'qa' in title or 'quality' in title or 'test' in title:
                    title = 'qa engineer'
                else:
                    title = 'software engineer'
            if pre_title is not '':
                title = pre_title + ' ' + title

        line_str += title
        attr_dict['title'].append(title)
    else:
        line_str += ''

    line_str += '\n'
    return unicode(line_str).encode('utf-8')

def searchPage(opener, config_file, page_num, person_info, temp_dir, output_file):
    url = "http://www.linkedin.com/vsearch/pj"
    
    search_array = readJsonObjFromFile(config_file, "searchRules")
    search_param = {}
    if search_array is not None:
        num = len(search_array)
        
        if num > 0:
            for item in search_array:
                search_param[getElementFromJson(item, "fieldName")] = getElementFromJson(item, "fieldValue")
            search_param['page_num'] = page_num

        else:
            print "search rules cannot be empty"
            return 0
    else:
        print "search rules cannot be None"
        return 0

    res_content = sendRequest(opener, url, search_param, None, None)

    json_obj = json.loads(res_content)

    resultCount = getElementFromJson(json_obj, 'content->page->voltron_unified_search_json->search->baseData->resultCount')
    print "result count is: " , resultCount

    if resultCount > 0:

        results = getElementFromJson(json_obj, 'content->page->voltron_unified_search_json->search->results') 
        if results is not None:
            num = len(results)
            if num > 0:
                for item in results:
                    person = getElementFromJson(item, 'person')
                    processPerson(opener, person, person_info, temp_dir, output_file)
            else:
                resultCount = 0
        else:
            resultCount = 0

    return resultCount

def crawel(opener, config_file, output_file, temp_dir):
    page_num = 1
    result_count = 1
    person_info = []
    output = open(output_file, "ab")

    global person_num
    global attr_dict
    global nameList
    
    attr_dict = {}
    complete_name_list = ['degree']
    complete_name_list.extend(nameList)
    complete_name_list.append('title')
    
    for fn in complete_name_list:
        attr_dict[fn] = []

    person_num = 0
    
    output.write("@RELATION PERSON\n")
    output.write("@DATA\n")
    while result_count > 0:
    #while page_num == 1:
        result_count = searchPage(opener, config_file, page_num, person_info, temp_dir, output)
        print "Finished page number is: ", page_num
        page_num += 1
        
    for fn in complete_name_list:
        attr = ",".join(set(map(lambda x:x.lower(),attr_dict[fn])))
        line_str = "@ATTRIBUTE " + fn + " {" + attr + "}\n"
        output.write(unicode(line_str).encode('utf-8'))

    output.close()
    return

def main():
    config_file, output_file, temp_dir = getConfig()
    opener = init(config_file, temp_dir)
    login(opener, config_file)
    crawel(opener, config_file, output_file, temp_dir)
    return

if (__name__ == '__main__'):
    main()
