import glob
import os
import time
import json
import warnings
import multiprocessing
from itertools import chain
from bs4 import BeautifulSoup


# ## Function to extract relevant xml tags

# In[2]:


def extract_xml_tag(input_xml, filename):
    """
        sort out input_soup tags and return list of values
        INPUT: input_xml is the content read from a xml file
        RETURN two dictionaries, one for short information and one for abstracts
    """
    # dictionaries to record data
#    shortinfo = {}
    award_elements = {}
    abstract = {}
    
    # make soup and extract tags
    input_soup = BeautifulSoup(input_xml, 'lxml-xml')
    
    # anything fails, that means file structure is corrupted
    try:
        # award identification (keep it as top level key value)
        award_id_string = input_soup.find('AwardID').text
        try:
            award_id = int(award_id_string)
            award_elements['award_id'] = award_id
        except:
            award_id = award_id_string
            award_elements['award_id'] = award_id
            warnings.warn('Could NOT convert award id {} to an integer'.format(award_id_string), UserWarning)

        # create dictionary for short information
#        award_elements = {}
        
        # Title, dates, amount
        award_elements['title'] = input_soup.find('AwardTitle').text
        award_elements['eff_date'] = input_soup.find('AwardEffectiveDate').text
        award_elements['exp_date'] = input_soup.find('AwardExpirationDate').text 
        amount_string = input_soup.find('AwardAmount').text
        # attempt to convert amount to integer
        try:
            award_elements['amount'] = int(amount_string)
        except:
            award_elements['amount'] = amount_string
            warnings.warn('Could NOT convert awarded amount {} to an integer'.format(amount_string), UserWarning)

        # award type
        award_elements['award_instr'] = input_soup.find('AwardInstrument').find('Value').text

        # organization info
        org_tree = input_soup.find('Organization')
        org_code_string = org_tree.find('Code').text
        try:
            award_elements['org_code'] = int(org_code_string)
        except:
            award_elements['org_code'] = org_code_string
            warnings.warn('Could NOT convert org code {} to an integer'.format(org_code_string), UserWarning)

        award_elements['org_direct'] = org_tree.find('Directorate').find('LongName').text
        award_elements['org_div'] = org_tree.find('Division').find('LongName').text

        # nsf officer who approved grant
        award_elements['nsf_officer'] = input_soup.find('ProgramOfficer').find('SignBlockName').text

        # record all investigator
        award_elements['Investigator'] = []
        inv_trees = input_soup.Award.find_all('Investigator', recursive=False)
        for inv in inv_trees:
            this_investigator = {}
            this_investigator['FirstName'] =  inv.find('FirstName').text
            this_investigator['LastName'] =  inv.find('LastName').text
            this_investigator['Role'] = inv.find('RoleCode').text
            award_elements['Investigator'].append(this_investigator)

        # record all participating institutions
        award_elements['Institution'] = []
        institution_trees = input_soup.Award.find_all('Institution', recursive=False)
        for ins in institution_trees:
            this_institution = {}
            this_institution['Name'] =  ins.find('Name').text
            this_institution['StreetAddress'] =  ins.find('StreetAddress').text
            this_institution['City'] = ins.find('CityName').text
            this_institution['State'] = ins.find('StateCode').text
            this_institution['Country'] = ins.find('CountryName').text
            award_elements['Institution'].append(this_institution)

        # record program elements (research qualifier)
        award_elements['ProgramElement'] = []
        progele_trees = input_soup.Award.find_all('ProgramElement', recursive=False)
        for pe in progele_trees:
            this_progelement = {}
            this_progelement['Text'] =  pe.find('Text').text
            code_string =  pe.find('Code').text
            try:
                this_progelement['Code'] = int(code_string)
            except:
                this_progelement['Code'] = code_string
                warnings.warn('Could NOT convert Program element code {} to an integer'.format(code_string), UserWarning)
            award_elements['ProgramElement'].append(this_progelement)

#        # add award id as top level key
#        shortinfo[award_id] = award_elements
        
        # take care of abstract
        abstract['award_id'] = award_id
        this_abstract = input_soup.find('AbstractNarration').text
        # make sure abstract is not empty (tag can exist but no text associated with it)
        if not not this_abstract:
            abstract['abstract'] = this_abstract
    except:
        warnings.warn(
                'File {} does not comply with xml schema! It will be skipped'.format(os.path.basename(filename)), UserWarning)
        
    # return both dictionaries
#    return shortinfo, abstract
    return award_elements, abstract


# In[3]:


def read_extract(file_list):
    """
        Read files and extract info using Beautiful soup
        INPUT: file_list is a list of file names
        RETURN two list of dictionaries (short info and abstract)
    """
    # list of dictionaries for short element
    awards_short_elements = []
    # list of dictionaries for abstract
    awards_abstract = []
    
    # read data in each xml file
    for thisfile in file_list:

        with open(thisfile, encoding='utf-8') as f:
            xml_text = f.read()
        
        # extract info from xml
        award_info, award_text = extract_xml_tag(xml_text, thisfile)
        
        # populate list of dictionaries unless it is empty
        if not not award_info:
            awards_short_elements.append(award_info)
        if not not award_text:
            awards_abstract.append(award_text)
        
    return awards_short_elements, awards_abstract

# ## Multiprocessing main loop

# In[ ]:


if __name__ == "__main__":
    # get start time of timer for processing time
    start_time = time.time()
    
#    # make sure output csv files do not exist, otherwise delete them
#    short_elements_output = os.path.join(os.pardir,'data', 'interim', 't_short_elements.json')   
#    if os.path.isfile(short_elements_output):
#        os.remove(short_elements_output)
#    
#    abstract_output = os.path.join(os.pardir,'data', 'interim', 't_abstracts.json')
#    if os.path.isfile(abstract_output):
#        os.remove(abstract_output)
    
    # number of processes (quad cores have 8 CPU, 1 CPU = 1 process at most)
    NUM_PROCESS = 8
    
    # file count and cumulative file count read
    cumfilecount = 0
    
    # number of files to distribute to each task
    num_file_partition = 200
    
    # year range for url, REMINDER: start at 1960
    years = range(1960,2017+1)
    
    # top level list of dict (json array)
    top_json_short = []
    top_json_abstract = []
    
    # create pool
    with multiprocessing.Pool(processes=NUM_PROCESS, maxtasksperchild=None) as pool:

        for ny,y in enumerate(years):
    
            # number of files read in current folder
            filecount = 0
    
            # list all xml files in current folder
            xml_list = glob.glob(os.path.join(os.pardir, 'data', 'raw', str(y), '*.xml'))
    
            # partition list of files
            intervals = range(0,len(xml_list), num_file_partition)
            xml_partition = [ xml_list[nfile:nfile+num_file_partition] for nfile in intervals ]
    
            # number of task to distribute among cores
            num_partition = len(xml_partition)
    
            # number of file in last task (most likely different from num_file_partition)
            num_lastfile_partition = len(xml_partition[-1])
    
            # feed pool with all files from current year by partition
            pool_results = pool.map(read_extract, xml_partition)
            
            # pool_results is a list of num_partition elements
            # each element is a tuple (short, abstract)
            # short and abstract each contains a list of dict
            unstacked_pool_results = list(chain.from_iterable(pool_results))
            
            # unstacked_pool_results is a list short and abstract alternatively
            # slice list to separate short and abstract
            pool_short = unstacked_pool_results[::2]
            pool_abstract = unstacked_pool_results[1::2]
    
            # pool_short has num_file_partition list of dictionary
            # consolidate all list of dict into one
            # and extend our existing list
            top_json_short.extend(list(chain.from_iterable(pool_short)))
            top_json_abstract.extend(list(chain.from_iterable(pool_abstract)))
    
#            # write dict to file
#            with open(short_elements_output, "a", encoding='utf-8') as f:
#                json.dump(short_element, f, ensure_ascii=False)
#    
#            with open(abstract_output, "a", encoding='utf-8') as f:
#                json.dump(abstract, f, ensure_ascii=False)
    
            # file counters
            filecount += (num_partition - 1)*num_file_partition + num_lastfile_partition
            cumfilecount += filecount
    
            # print progress
            print('\rYear {}, File #{:6d},Total File {:6d}'.format(y,
                  filecount, cumfilecount) ,end='', flush=True)

    # write list of dict to file
    short_elements_output = os.path.join(os.pardir,'data', 'interim', 'short_elements.json')   
    with open(short_elements_output, "w", encoding='utf-8') as f:
        json.dump(top_json_short, f, ensure_ascii=False)

    abstract_output = os.path.join(os.pardir,'data', 'interim', 'abstracts.json')
    with open(abstract_output, "w", encoding='utf-8') as f:
        json.dump(top_json_abstract, f, ensure_ascii=False)

    # closing print statement
    print('\rYear {}, File #{:6d},Total File {:6d}'.format(y, filecount, cumfilecount), end='\n', flush=True)
    print("--- %s seconds ---" % (time.time() - start_time))

