import urllib2, urllib, socket, json, cookielib, os
from cStringIO import StringIO
import codecs
from optparse import OptionParser

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
    output_file = "temp/result.json"
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



def processPerson(opener, person, person_info, temp_dir):
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
    
    person_obj['headLine'] = getElementFromJson(tc_obj, 'content->BasicInfo->basic_info->memberHeadline') 

    person_obj['previousCompanies'] = []

    pre_positions = getElementFromJson(tc_obj, 'content->TopCard->positionsMpr->topPrevious')
    if pre_positions is not None:
        num =  len(pre_positions)        
        if num > 0:
            for item in pre_positions:
                person_obj['previousCompanies'].append(item['companyName'])

    person_obj['educations'] = []

    top_edu = getElementFromJson(tc_obj, 'content->TopCard->educationsMpr->topEducations') 
    if top_edu is not None:
        num = len(top_edu)
        if num > 0:
            for item in top_edu:
                person_obj['educations'].append({'schoolName': getElementFromJson(item, 'schoolName'), 
                    'major': getElementFromJson(item, 'fieldOfStudy'), 'degree':
                    getElementFromJson(item, 'degree') })

    more_edu = getElementFromJson(tc_obj, 'content->TopCard->educationsMpr->moreEducations')
    if more_edu is not None:
        num = len(more_edu)
        if num > 0:
            for item in top_edu:
                person_obj['educations'].append({'schoolName': getElementFromJson(item, 'schoolName'), 'major': 
                getElementFromJson(item, 'fieldOfStudy'), 'degree': getElementFromJson(item, 'degree') })       

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
    
    langData = getElementFromJson(profile_obj, 'content->Languages->languages->languagesData')
    if langData is not None:
        num = len (langData)
        if num > 0:
            for item in langData:
                person_obj['languages'].append({'lang': getElementFromJson(item, 'lang'), 
                    'level': getElementFromJson(item, 'proficiencyData')})

    person_obj['skills'] = []
    skills = getElementFromJson(profile_obj, 'content->Skills->skillsMpr->skills')

    if skills is not None:
        num = len(skills)
        if num > 0:
            for item in skills:
                person_obj['skills'].append({'skillName': getElementFromJson(item, 'name'), 
                    'endorsementCount': getElementFromJson(item, 'endorsementCount')})

    print person_obj
    person_info.append(person_obj)
    return

def searchPage(opener, config_file, page_num, person_info, temp_dir):
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

    resultCount = getElementFromJson(json_obj, 'content->voltron_unified_search_json->search->baseData->resultCount')
    print "result count is: " , resultCount

    if resultCount > 0:

        results = getElementFromJson(json_obj, 'content->voltron_unified_search_json->search->results') 
        if results is not None:
            num = len(results)
            if num > 0:
                for item in results:
                    person = getElementFromJson(item, 'person')
                    processPerson(opener, person, person_info, temp_dir)
            else:
                resultCount = 0
        else:
            resultCount = 0

    return resultCount

def crawel(opener, config_file, output_file, temp_dir):
    page_num = 1
    result_count = 1
    person_info = []
    while result_count > 0:
        result_count = searchPage(opener, config_file, page_num, person_info, temp_dir)
        page_num += 1
        print "Finished page number is: ", page_num
    
    result_str = json.dumps(person_info)
    open(output_file, "w").write(result_str)
    return

def main():
    config_file, output_file, temp_dir = getConfig()
    opener = init(config_file, temp_dir)
    login(opener, config_file)
    crawel(opener, config_file, output_file, temp_dir)
    return

if (__name__ == '__main__'):
    main()
