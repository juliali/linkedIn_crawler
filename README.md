linkedIn_crawler
================

A python script to run search on linkedIn and collect the result in JSON format.

So far, the script is only work for people search and only provide id, first name, last name, languages, previous companies, educations and skills for each searched person.

To run this script you need to create your own configuration file (the default one is conf/config.json). Please follow the format of the default configuration file to create your own. 

1. You need to define the proxy info. If you don't need a proxy, just leave the 'proxy' array in the config.json empty.

2. You need to input your login email and password in the 'login' element of config.json.

3. You need to input your own search rules. The rules ought to be parameters for the request of Advanced search on linkedIn. You can conduct a search with browser and catch the request with Chrome developer tool or Firefox firebug, and put those request parameters into the 'searchRules' array in config.json.


naive bayes classifer
=====================

A python script to set up a naive bayes classifer to work on the data crawled by linkedin_crawler.

The linkedin_crawler will generate arff files as final output, and they will be the training/testing data set.

e.g.
    1) add your own login email and password in conf/config.json
    2) run the following commands under the current dir
    $python ./linkedin_crawler.py
    $python ./classifer.py --train-file=temp/person_attr.arff 
