# -*- coding: utf-8 -*-
"""
Created on Sun May 27 23:19:47 2018

@author: herma
"""


import re
# customize CountVectorizer to add stemmer or lemmatizer
from sklearn.feature_extraction.text import CountVectorizer
# lemmatization to convert plurals words to singular word
from nltk.stem.wordnet import WordNetLemmatizer
Lem = WordNetLemmatizer()



class CustomVectorizer(CountVectorizer):
    """
    Create a class that superseed sklearn CountVectorizer()
    """
        
    # override build_tokenizer() that is part of CountVectorizer()
    def build_tokenizer(self):
        # tokenize is the return value of build_tokenizer() from CountVectorizer
        # tokenize is a lambda function that intends to receive a string
        tokenize = super(CustomVectorizer, self).build_tokenizer()
        
        # tokenize(doc) is a list of words (=tokens)
        return lambda doc: list(custom_lem(tokenize(doc)))


def custom_lem(tokens):
    """
        Generator function for enhanced tokenizer
    """
    for t in tokens:
        t = Lem.lemmatize(t)
        # returns one word each time custom_lem() gets called
        # custom_lem() gets called by list iteratively
        yield t


def rm_tag_http(doc):
    """
    Custom preprocessor for CountVectorizer
    Removes html tags and http links
    """
    
    # remove all <any character one or more times>
    # ? is necessary (non greedy) otherwise it will continue to match after '>'
    tagFree = re.sub(r'<.+?>', '', doc)
    
    # remove all website links starting with http (or https, h,ht,htt will be
    # matched as a side effect) followed by any non white space characters
    return re.sub(r'https?\S*', '', tagFree)


#### The Main program, can be used as a script or as a module
if __name__ == "__main__":
	pass

